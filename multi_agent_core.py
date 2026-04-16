"""多智能体核心逻辑 - 支持直播策划与技术主播协作，含 TTS 功能。"""

import re
import asyncio
import os
import edge_tts
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from typing import Any, Dict, List, Optional, Tuple
from tools.tools import search_industry_news

load_dotenv()


class AgentCallbackHandler(BaseCallbackHandler):
    """通用回调处理器，用于捕获 Agent 各个阶段的思考过程。"""

    def __init__(self, container=None):
        self.thought_steps = []
        self.container = container
        self.current_step = ""

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        tool_name = serialized.get("name", "未知工具")
        display_input = input_str[:200] + "..." if len(input_str) > 200 else input_str
        step = {
            "icon": "🔍",
            "title": "调用工具",
            "content": f"正在调用工具：`{tool_name}`\n\n参数：`{display_input}`"
        }
        self.thought_steps.append(step)

    def on_tool_end(self, output: Any, **kwargs):
        try:
            output_str = str(output) if not isinstance(output, str) else output
            display_output = output_str[:500] + "..." if len(output_str) > 500 else output_str
        except:
            display_output = str(output)
        step = {
            "icon": "✅",
            "title": "工具完成",
            "content": f"工具返回结果：\n\n{display_output}"
        }
        self.thought_steps.append(step)

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        step = {
            "icon": "🧠",
            "title": "LLM 推理",
            "content": "正在分析问题并制定解决方案..."
        }
        self.thought_steps.append(step)

    def on_llm_end(self, response: Any, **kwargs):
        step = {
            "icon": "✨",
            "title": "推理完成",
            "content": "正在生成回答..."
        }
        self.thought_steps.append(step)


def create_llm():
    """创建统一的 LLM 实例。"""
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")
    
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
    )
    return llm


def create_director_agent(llm):
    """创建直播策划 Agent (Director)。"""
    tools = [search_industry_news]
    director_agent = create_agent(llm, tools)
    return director_agent


def run_director_agent(user_input: str, callback: AgentCallbackHandler = None):
    """运行直播策划 Agent。"""
    llm = create_llm()
    director = create_director_agent(llm)

    director_prompt = f"""你是一位专业的直播策划编导，擅长规划技术类直播的内容结构。

请根据用户的需求，输出一份【直播大纲与分镜】。

用户需求：{user_input}

要求：
1. 先调用 search_industry_news 工具查询最新行业动态
2. 基于调研结果，输出一份结构化的直播大纲
3. 大纲应包含：直播主题、核心内容模块、时长分配、互动环节设计

请开始策划并输出完整的直播大纲。"""

    response = director.invoke(
        {"messages": [("user", director_prompt)]},
        config={"callbacks": [callback]} if callback else {},
    )

    return response["messages"][-1].content


def extract_script_text(anchor_output: str) -> str:
    """从技术主播的输出中提取纯口播文本（去除代码块）。"""
    lines = anchor_output.split('\n')
    script_lines = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            script_lines.append(line)

    script_text = '\n'.join(script_lines)
    script_text = re.sub(r'\n{3,}', '\n\n', script_text)
    script_text = script_text.strip()

    return script_text


def extract_obs_commands(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """提取 OBS 指令，同时清洗文本。

    Returns:
        (清洗后的文本, OBS指令列表)
    """
    obs_commands = []
    lines = text.split('\n')
    cleaned = []

    obs_pattern = r'\[OBS_CMD:\s*([^]]+)\]'

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        matches = re.findall(obs_pattern, line)
        for scene in matches:
            obs_commands.append({
                "order": len(obs_commands) + 1,
                "scene": scene.strip(),
                "original_line": line[:50]
            })

        clean_line = re.sub(obs_pattern, '', line)

        # 过滤规则1：过滤所有括号内的内容（包括半角和全角括号，使用DOTALL模式匹配跨行内容）
        clean_line = re.sub(r'\(.*?\)', '', clean_line, flags=re.DOTALL)  # 过滤半角括号内容
        clean_line = re.sub(r'（.*?）', '', clean_line, flags=re.DOTALL)  # 过滤全角括号内容
        
        # 如果过滤后变成空行，则跳过
        if not clean_line.strip():
            continue

        # 过滤规则2：过滤纯【】内的内容（如"【极客风口播逐字稿】"）
        if re.match(r'^【[^】]*】$', clean_line):
            continue

        # 过滤规则3：过滤特定标题（如"实战代码 Demo"、"极客风口播逐字稿"）
        if re.search(r'实战代码|Demo|极客风口播逐字稿', clean_line):
            continue

        # 过滤规则4：过滤Markdown标题
        clean_line = re.sub(r'^#{1,6}\s*', '', clean_line)

        # 过滤规则5：过滤时间戳
        clean_line = re.sub(r'^\d{1,2}:\d{2}(-\d{1,2}:\d{2})?\s*', '', clean_line)

        # 过滤规则6：过滤冒号前缀
        clean_line = re.sub(r'^.{1,6}[：:]\s*', '', clean_line)

        # 过滤规则7：过滤特殊字符
        clean_line = re.sub(r'[*#>`=_-]', '', clean_line)

        # 过滤规则8：过滤OBS指令残留
        clean_line = re.sub(r'\[.*?\]', '', clean_line)

        clean_line = clean_line.strip()

        # 过滤规则9：过滤空行和短行
        if clean_line and len(clean_line) > 1:
            cleaned.append(clean_line)

    text = ' '.join(cleaned)

    text = re.sub(r'\s+', ' ', text)

    return text.strip(), obs_commands


def clean_text_for_tts(text: str) -> str:
    """清洗文本，只保留真人念白内容（保留 OBS 指令用于提取）。"""
    cleaned_text, _ = extract_obs_commands(text)
    return cleaned_text


async def generate_speech_async(text: str, output_file: str = "live_audio.mp3", max_retries: int = 3) -> str:
    """异步生成 TTS 语音，使用更有活力的参数。"""
    last_error = None
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(
                text,
                voice="zh-CN-YunxiNeural",
                rate="+10%",
                volume="+20%"
            )
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2)

    raise Exception(f"TTS语音生成失败（已重试{max_retries}次）: {last_error}")


def generate_speech(text: str, output_file: str = "live_audio.mp3") -> str:
    """同步调用 TTS 生成语音。"""
    try:
        # 检查是否已经存在事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果在已有事件循环中，创建新的事件循环
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, generate_speech_async(text, output_file))
                return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，可以直接使用asyncio.run()
            return asyncio.run(generate_speech_async(text, output_file))
    except Exception as e:
        print(f"TTS生成错误: {e}")
        return None


def run_tech_anchor_agent(outline: str, callback: AgentCallbackHandler = None):
    """运行技术主播 Agent。"""
    llm = create_llm()

    anchor_system_prompt = """你是一位资深技术主播，擅长将复杂的技术内容转化为生动有趣的口播话术。

你的任务是基于【直播大纲】输出：
1. 可执行的实战代码 Demo
2. 配套的【极客风口播逐字稿】

重要：直播间场景控制指令（OBS控制）：
- 我们的直播间只有三个物理场景：
  - [OBS_CMD: 主播近景] 用于开场、聊天、总结
  - [OBS_CMD: 代码实战] 用于讲解代码、演示
  - [OBS_CMD: 数据图表] 用于分析趋势、展示数据
- 在剧本中适当位置插入上述指令，格式必须严格为 [OBS_CMD: 场景名称]
- 建议每2-3分钟切换一次画面，保持观众注意力

要求：
- 代码要简洁、可运行、有注释
- 口播稿要口语化、接地气、有激情
- 将技术亮点与实际应用场景结合
- 适当加入一些"梗"和互动话术

请直接输出代码块和逐字稿，不要再调用任何工具。"""

    anchor_prompt = ChatPromptTemplate.from_messages([
        ("system", anchor_system_prompt),
        ("user", "【直播大纲】:\n{outline}"),
    ])

    chain = anchor_prompt | llm

    if callback:
        callback.thought_steps.append({
            "icon": "🧠",
            "title": "LLM 推理中",
            "content": "技术主播正在基于大纲生成代码和话术（含OBS指令）..."
        })

    response = chain.invoke({"outline": outline})

    if callback:
        callback.thought_steps.append({
            "icon": "✨",
            "title": "生成完成",
            "content": "代码和话术已生成"
        })

    return response.content


def run_tutor_agent(user_question: str, course_material: str, chat_history: list = None, callback: AgentCallbackHandler = None):
    """运行 VIP 课后助教 Agent - 基于课程讲义回答学员问题。"""
    llm = create_llm()

    chat_history_text = ""
    if chat_history:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            chat_history_text += f"{role}: {content}\n"

    tutor_system_prompt = f"""你是一位资深 AI 编程导师，专注于帮助学员解答课程相关的问题。

## 核心原则
1. **严格基于讲义回答**：你只能基于以下提供的《直播课程讲义》内容来回答学员的问题
2. **防幻觉**：如果学员问的问题超出讲义范围，请委婉拒绝，并引导他们关注后续课程
3. **专业耐心**：用专业、耐心、鼓励的方式回答问题

## 回答格式要求
- 优先引用讲义中的具体内容
- 如果需要代码示例，必须从讲义中提取或基于讲义知识编写
- 适当使用 Markdown 格式美化回答

## 直播课程讲义（私有背景知识）
{course_material}

---
"""

    if chat_history_text:
        full_prompt = tutor_system_prompt + f"\n\n对话历史：\n{chat_history_text}\n\n学员最新问题：{user_question}"
    else:
        full_prompt = tutor_system_prompt + f"\n\n学员问题：{user_question}"

    if callback:
        callback.thought_steps.append({
            "icon": "🧠",
            "title": "助教思考中",
            "content": "VIP 助教正在基于课程讲义为你解答..."
        })

    response = llm.invoke(full_prompt)

    if callback:
        callback.thought_steps.append({
            "icon": "✨",
            "title": "回答完成",
            "content": "助教已生成回答"
        })

    return response.content if hasattr(response, 'content') else str(response)


def parse_business_assets(agent_output: str) -> tuple:
    """解析商业运营 Agent 的输出，切分为三份资产。"""
    import re

    asset_1_pattern = r"【资产一开始】(.*?)【资产一结束】"
    asset_2_pattern = r"【资产二开始】(.*?)【资产二结束】"
    asset_3_pattern = r"【资产三开始】(.*?)【资产三结束】"

    asset_1_match = re.search(asset_1_pattern, agent_output, re.DOTALL)
    asset_2_match = re.search(asset_2_pattern, agent_output, re.DOTALL)
    asset_3_match = re.search(asset_3_pattern, agent_output, re.DOTALL)

    asset_1 = asset_1_match.group(1).strip() if asset_1_match else ""
    asset_2 = asset_2_match.group(1).strip() if asset_2_match else ""
    asset_3 = asset_3_match.group(1).strip() if asset_3_match else ""

    return asset_1, asset_2, asset_3


def run_business_agent(full_script: str, callback: AgentCallbackHandler = None):
    """运行商业运营 Agent - 顶级知识IP操盘手，一次性生成三种商业资产。"""
    llm = create_llm()

    business_system_prompt = """你是一位**顶级知识IP操盘手**，拥有10年以上知识付费和短视频营销经验，曾打造多个百万级变现的知识IP。

你的核心能力是：将一场直播的原始逐字稿，快速转化为可变现的商业资产。

## 角色定位
- 知识IP商业化专家
- 短视频营销策划专家
- 内容矩阵架构师

## 任务要求
基于用户提供的直播逐字稿，你需要**一次性生成三份商业资产**：

---

### 【资产一】直播配套课程 Markdown 讲义

要求：
- 结构化输出，使用 Markdown 格式
- 包含课程大纲、核心知识点、代码片段总结
- 每个章节要有"知识点总结"和"实战练习"
- 适合作为独立课程售卖给学员

---

### 【资产二】小红书爆款图文引流文案

要求：
- 格式：标题 + 正文 + 引导评论
- 必须使用 Emoji（💡、🔥、📌、⚡、🎯 等）
- 标题要引发焦虑/好奇，例如：
  - "90%的程序员不知道的AI编程技巧"
  - "为什么你写的代码总是有bug？"
  - "靠这个方法，我3天学会了..."
- 正文结构：痛点引入 → 解决方案 → 价值钩子 → 引导私域
- 结尾引导评论："你怎么看？评论区聊聊"

---

### 【资产三】抖音 30 秒短视频脚本

要求：
- 提取直播中最炸裂、最吸引眼球的一个观点
- 分镜结构：画面描述 + 口播词 + 时长
- 总时长控制在 30 秒以内
- 口播词要口语化、节奏感强、情绪饱满
- 最后要有互动引导（"关注我，下期更精彩"）

---

## 输出格式要求

请严格按照以下分隔符格式输出，不要添加任何额外说明：

【资产一开始】
[你的课程讲义 Markdown 内容]
【资产一结束】

【资产二开始】
[你的小红书文案内容]
【资产二结束】

【资产三开始】
[你的短视频脚本内容]
【资产三结束】

---

直播逐字稿如下：
""" + full_script + """

请开始生成三份商业资产。"""

    if callback:
        callback.thought_steps.append({
            "icon": "🧠",
            "title": "商业资产生成中",
            "content": "顶级知识IP操盘手正在为你打造变现资产..."
        })

    response = llm.invoke(business_system_prompt)

    if callback:
        callback.thought_steps.append({
            "icon": "✨",
            "title": "资产生成完成",
            "content": "三份商业资产已生成完毕"
        })

    return response.content


def run_field_control_agent(danmu: str, outline: str, callback: AgentCallbackHandler = None):
    """运行场控答疑 Agent。"""
    llm = create_llm()

    field_control_system_prompt = f"""你是一位反应极快、技术功底深厚的直播场控助教。

你的任务是用简短、口语化、带有极客幽默感的方式回答观众的问题。

人设要求：
- 回答必须简短，不超过3句话
- 口语化、接地气
- 适当带点极客幽默感
- 语气热情、自信

背景知识（直播大纲）：
{outline}

请直接回答观众的问题，不要调用任何工具。"""

    field_control_prompt = ChatPromptTemplate.from_messages([
        ("system", field_control_system_prompt),
        ("user", "观众弹幕：{danmu}"),
    ])

    chain = field_control_prompt | llm

    if callback:
        callback.thought_steps.append({
            "icon": "🧠",
            "title": "场控回复中",
            "content": "场控答疑Agent正在生成回复..."
        })

    response = chain.invoke({"danmu": danmu})

    if callback:
        callback.thought_steps.append({
            "icon": "✨",
            "title": "回复完成",
            "content": "场控答疑已完成"
        })

    return response.content


def run_judge_agent(full_script: str, danmu_history: str = "", callback: AgentCallbackHandler = None):
    """运行 LLM-as-a-Judge 裁判 Agent - 直播全链路智能复盘。"""
    llm = create_llm()

    danmu_section = f"\n\n## 弹幕互动记录\n{danmu_history}" if danmu_history else "\n\n## 弹幕互动记录\n（本场直播暂无弹幕互动记录）"

    judge_system_prompt = f"""你是一位拥有**十年经验**的顶级直播操盘手，曾操盘过多场百万级观看的技术直播，对内容质量把控极为严格。

## 你的角色
- 直播内容质量评审专家
- 观众行为分析专家
- 商业转化策划专家

## 任务要求
请仔细审查本场直播的剧本和互动记录，从**三个维度**进行严格打分（满分100）：

### 评分维度
1. **极客硬核度** - 技术深度、代码实战含量、干货程度
2. **互动引导率** - 互动设计、话术引导、观众参与度
3. **商业转化埋点** - 课程引流、私域导流、变现环节设计

## 输出格式要求
请严格按照以下分隔符格式输出结构化报告：

【核心指标雷达】
极客硬核度得分：XX分
互动引导率得分：XX分
商业转化埋点得分：XX分

【高光时刻】
[做得好的地方具体描述]

【流失风险点】
[可能导致观众划走的无聊片段或逻辑漏洞]

【下期优化建议】
[针对风险点给出的具体修改方案]

---
直播逐字稿：
{full_script}
{danmu_section}

请开始评审并输出报告。"""

    if callback:
        callback.thought_steps.append({
            "icon": "🧠",
            "title": "复盘评审中",
            "content": "LLM 裁判正在对直播进行全链路复盘..."
        })

    response = llm.invoke(judge_system_prompt)

    if callback:
        callback.thought_steps.append({
            "icon": "✨",
            "title": "复盘完成",
            "content": "体检报告已生成"
        })

    return response.content if hasattr(response, 'content') else str(response)


def parse_judge_report(agent_output: str) -> dict:
    """解析裁判 Agent 的输出，提取各部分内容。"""
    import re

    result = {
        "radar": "",
        "highlights": "",
        "risks": "",
        "suggestions": ""
    }

    radar_pattern = r"【核心指标雷达】(.*?)(?=【|$)"
    highlights_pattern = r"【高光时刻】(.*?)(?=【流失风险点】|$)"
    risks_pattern = r"【流失风险点】(.*?)(?=【下期优化建议】|$)"
    suggestions_pattern = r"【下期优化建议】(.*?)$"

    radar_match = re.search(radar_pattern, agent_output, re.DOTALL)
    highlights_match = re.search(highlights_pattern, agent_output, re.DOTALL)
    risks_match = re.search(risks_pattern, agent_output, re.DOTALL)
    suggestions_match = re.search(suggestions_pattern, agent_output, re.DOTALL)

    if radar_match:
        result["radar"] = radar_match.group(1).strip()
    if highlights_match:
        result["highlights"] = highlights_match.group(1).strip()
    if risks_match:
        result["risks"] = risks_match.group(1).strip()
    if suggestions_match:
        result["suggestions"] = suggestions_match.group(1).strip()

    return result
