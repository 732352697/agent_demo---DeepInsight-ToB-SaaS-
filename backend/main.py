"""
DeepInsight 2.0 - FastAPI 后端核心引擎
API First 架构，彻底与 Streamlit 前端解耦

启动命令: uvicorn backend.main:app --reload --port 8000
访问文档: http://localhost:8000/docs
"""

import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# 添加项目根目录到 Python 路径，以便导入 multi_agent_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_core import (
    AgentCallbackHandler,
    run_director_agent,
    run_tech_anchor_agent,
    run_tutor_agent,
    run_business_agent,
    run_judge_agent,
    extract_obs_commands,
    parse_business_assets,
    parse_judge_report,
)
from backend.schemas import (
    LiveScriptRequest,
    LiveScriptResponse,
    TutorChatRequest,
    TutorChatResponse,
    BusinessAssetsRequest,
    BusinessAssetsResponse,
    JudgeReportRequest,
    JudgeReportResponse,
    HealthCheckResponse,
    ActionQueueItem,
)


# ==================== FastAPI 应用初始化 ====================

app = FastAPI(
    title="DeepInsight AI 核心引擎",
    description="""DeepInsight 2.0 商业级后端 API
    
## 核心能力
- 🎙️ **直播策划**: 基于 AI Agent 的直播大纲与脚本生成
- 👨‍🏫 **VIP 助教**: 基于课程讲义的智能问答
- 💰 **商业资产**: 一键生成课程讲义、小红书文案、短视频脚本
- 📊 **直播复盘**: LLM-as-a-Judge 智能评审

## 技术栈
- FastAPI + Pydantic
- DeepSeek LLM
- LangChain Agent Framework
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ==================== CORS 跨域配置 ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8502",
        "http://localhost:8503",
        "http://localhost:8504",
        "http://localhost:8505",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 中间件与异常处理 ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    print(f"[{datetime.now().isoformat()}] {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
    return response


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Pydantic 验证错误处理"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    print(f"[ERROR] {request.url.path} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": str(exc) if os.getenv("DEBUG") else None
            }
        }
    )


# ==================== 健康检查 ====================

@app.get("/health", response_model=HealthCheckResponse, tags=["系统"])
async def health_check():
    """健康检查接口"""
    return HealthCheckResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now()
    )


@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": "DeepInsight AI 核心引擎 API",
        "version": "2.0.0",
        "docs": "http://localhost:8000/docs"
    }


# ==================== 核心业务路由 ====================

@app.post(
    "/api/v1/live/generate",
    response_model=LiveScriptResponse,
    summary="生成直播脚本",
    description="接收直播主题，串联调用 Director Agent 和 Anchor Agent，返回完整的剧本和大纲数据",
    tags=["直播策划"]
)
async def generate_live_script(request: LiveScriptRequest):
    """
    ## 直播脚本生成流程
    
    1. **Director Agent**: 调用行业调研工具，生成直播大纲与分镜
    2. **Anchor Agent**: 基于大纲生成可执行代码 + 口语化逐字稿
    3. **OBS 指令提取**: 解析 `[OBS_CMD: 场景]` 标记，生成可执行队列
    
    ## 返回数据
    - `director_outline`: 直播大纲
    - `anchor_output`: 技术主播完整输出
    - `raw_script`: 清洗后的纯口播文本
    - `action_queue`: 可执行的剧本队列（文本+OBS指令）
    - `obs_commands`: OBS 场景切换指令列表
    """
    try:
        print(f"[API] 收到直播主题: {request.topic}")
        
        # 第一阶段：Director Agent 生成大纲
        director_callback = AgentCallbackHandler()
        director_outline = run_director_agent(request.topic, director_callback)
        
        # 第二阶段：Anchor Agent 生成代码和话术
        anchor_callback = AgentCallbackHandler()
        anchor_output = run_tech_anchor_agent(director_outline, anchor_callback)
        
        # 第三阶段：提取 OBS 指令和清洗文本
        cleaned_text, obs_commands = extract_obs_commands(anchor_output)
        
        # 第四阶段：构建 action_queue
        action_queue = build_action_queue(cleaned_text, obs_commands)
        
        return LiveScriptResponse(
            success=True,
            topic=request.topic,
            director_outline=director_outline,
            anchor_output=anchor_output,
            raw_script=cleaned_text,
            action_queue=action_queue,
            obs_commands=obs_commands
        )
        
    except Exception as e:
        print(f"[ERROR] generate_live_script: {str(e)}")
        raise HTTPException(status_code=500, detail=f"直播脚本生成失败: {str(e)}")


@app.post(
    "/api/v1/tutor/chat",
    response_model=TutorChatResponse,
    summary="VIP 课后助教问答",
    description="基于课程讲义，调用 Tutor Agent 回答学员问题",
    tags=["VIP 助教"]
)
async def tutor_chat(request: TutorChatRequest):
    """
    ## 助教问答流程
    
    1. 接收用户问题 + 课程讲义上下文
    2. 构建对话历史（支持多轮对话）
    3. 调用 Tutor Agent 生成回答
    
    ## 返回数据
    - `answer`: 助教回答内容
    """
    try:
        print(f"[API] 收到助教问答: {request.user_question[:50]}...")
        
        # 转换 chat_history 格式
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history
        ]
        
        # 调用 Tutor Agent
        tutor_callback = AgentCallbackHandler()
        answer = run_tutor_agent(
            user_question=request.user_question,
            course_material=request.course_material,
            chat_history=chat_history,
            callback=tutor_callback
        )
        
        return TutorChatResponse(
            success=True,
            answer=answer
        )
        
    except Exception as e:
        print(f"[ERROR] tutor_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"助教回答生成失败: {str(e)}")


@app.post(
    "/api/v1/business/generate",
    response_model=BusinessAssetsResponse,
    summary="生成商业变现资产",
    description="基于直播剧本，一键生成课程讲义、小红书文案、短视频脚本",
    tags=["商业资产"]
)
async def generate_business_assets(request: BusinessAssetsRequest):
    """
    ## 商业资产生成流程
    
    1. 将 action_queue 拼接为完整剧本
    2. 调用 Business Agent 生成三份资产
    3. 解析返回结果
    
    ## 返回数据
    - `course_material`: 直播配套课程 Markdown 讲义
    - `xiaohongshu`: 小红书爆款引流文案
    - `douyin`: 抖音 30 秒短视频分镜脚本
    """
    try:
        print(f"[API] 收到商业资产生成请求")
        
        # 拼接完整剧本
        full_script = assemble_script_from_queue(request.action_queue)
        
        if not full_script.strip():
            raise HTTPException(status_code=400, detail="剧本队列为空，无法生成商业资产")
        
        # 调用 Business Agent
        business_callback = AgentCallbackHandler()
        business_output = run_business_agent(full_script, business_callback)
        
        # 解析资产
        asset_1, asset_2, asset_3 = parse_business_assets(business_output)
        
        return BusinessAssetsResponse(
            success=True,
            course_material=asset_1 or "",
            xiaohongshu=asset_2 or "",
            douyin=asset_3 or ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] generate_business_assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"商业资产生成失败: {str(e)}")


@app.post(
    "/api/v1/judge/generate",
    response_model=JudgeReportResponse,
    summary="生成直播复盘报告",
    description="基于直播剧本和弹幕历史，调用 LLM-as-a-Judge 生成复盘报告",
    tags=["直播复盘"]
)
async def generate_judge_report(request: JudgeReportRequest):
    """
    ## 复盘报告生成流程
    
    1. 将 action_queue 拼接为完整剧本
    2. 格式化弹幕历史
    3. 调用 Judge Agent 生成三维评分报告
    
    ## 返回数据
    - `full_report`: 完整复盘报告
    - `radar_scores`: 雷达图分数（极客硬核度、互动引导率、商业转化埋点）
    """
    try:
        print(f"[API] 收到复盘报告生成请求")
        
        # 拼接完整剧本
        full_script = assemble_script_from_queue(request.action_queue)
        
        if not full_script.strip():
            raise HTTPException(status_code=400, detail="剧本队列为空，无法生成复盘报告")
        
        # 格式化弹幕历史
        danmu_section = f"\n\n## 弹幕互动记录\n{request.danmu_history}" if request.danmu_history else ""
        
        # 调用 Judge Agent
        judge_callback = AgentCallbackHandler()
        judge_output = run_judge_agent(full_script, request.danmu_history, judge_callback)
        
        # 解析报告
        report = parse_judge_report(judge_output)
        
        # 提取雷达图分数
        radar_scores = extract_radar_scores(report)
        
        return JudgeReportResponse(
            success=True,
            full_report=judge_output,
            radar_scores=radar_scores
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] generate_judge_report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"复盘报告生成失败: {str(e)}")


# ==================== 辅助函数 ====================

def build_action_queue(cleaned_text: str, obs_commands: List[Dict[str, Any]]) -> List[ActionQueueItem]:
    """从清洗后的文本和 OBS 指令构建 action_queue"""
    action_queue = []
    
    # 添加 OBS 指令
    for cmd in obs_commands:
        action_queue.append(ActionQueueItem(
            type="obs",
            scene=cmd.get("scene")
        ))
    
    # 添加文本内容（按句子分割）
    sentences = re.split(r'([。！？.!?])', cleaned_text)
    current_text = ""
    for sent in sentences:
        current_text += sent
        if sent in '。！？.!?':
            if current_text.strip():
                action_queue.append(ActionQueueItem(
                    type="text",
                    content=current_text.strip()
                ))
            current_text = ""
    if current_text.strip():
        action_queue.append(ActionQueueItem(
            type="text",
            content=current_text.strip()
        ))
    
    return action_queue


def assemble_script_from_queue(action_queue: List[ActionQueueItem]) -> str:
    """将 action_queue 拼接为完整剧本文本"""
    script_parts = []
    for item in action_queue:
        if item.type == "text" and item.content:
            script_parts.append(item.content)
    return "\n".join(script_parts)


def extract_radar_scores(report: Dict[str, str]) -> Dict[str, int]:
    """从复盘报告中提取雷达图分数"""
    scores = {
        "geek_score": 0,
        "interaction_score": 0,
        "commerce_score": 0
    }
    
    radar = report.get("radar", "")
    if not radar:
        return scores
    
    # 提取分数
    geek_match = re.search(r"极客硬核度得分[：:]\s*(\d+)", radar)
    if geek_match:
        scores["geek_score"] = int(geek_match.group(1))
    
    interaction_match = re.search(r"互动引导率得分[：:]\s*(\d+)", radar)
    if interaction_match:
        scores["interaction_score"] = int(interaction_match.group(1))
    
    commerce_match = re.search(r"商业转化埋点得分[：:]\s*(\d+)", radar)
    if commerce_match:
        scores["commerce_score"] = int(commerce_match.group(1))
    
    return scores


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
