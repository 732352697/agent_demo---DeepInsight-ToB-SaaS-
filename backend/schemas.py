"""
DeepInsight 2.0 - Pydantic 数据模型定义
定义 API 的输入输出格式，与前端解耦
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ==================== 直播策划 API ====================

class LiveScriptRequest(BaseModel):
    """直播脚本生成请求"""
    topic: str = Field(..., description="直播主题", min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "规划一场关于 Cursor AI 编程助手的直播"
            }
        }


class ActionQueueItem(BaseModel):
    """剧本队列中的单个动作项"""
    type: str = Field(..., description="动作类型: 'text' 或 'obs'")
    content: Optional[str] = Field(None, description="文本内容（type=text 时）")
    scene: Optional[str] = Field(None, description="OBS 场景名称（type=obs 时）")


class LiveScriptResponse(BaseModel):
    """直播脚本生成响应"""
    success: bool = Field(..., description="请求是否成功")
    topic: str = Field(..., description="直播主题")
    director_outline: str = Field(..., description="直播大纲与分镜")
    anchor_output: str = Field(..., description="技术主播输出（代码+话术）")
    raw_script: str = Field(..., description="清洗后的纯口播文本")
    action_queue: List[ActionQueueItem] = Field(..., description="可执行的剧本队列")
    obs_commands: List[Dict[str, Any]] = Field(default_factory=list, description="OBS 场景切换指令列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "topic": "规划一场关于 Cursor AI 编程助手的直播",
                "director_outline": "## 直播主题\n...",
                "anchor_output": "```python\n# 代码示例\n```\n\n【极客风口播逐字稿】\n...",
                "raw_script": "大家好，今天我们要聊的是...",
                "action_queue": [
                    {"type": "text", "content": "大家好..."},
                    {"type": "obs", "scene": "主播近景"}
                ],
                "obs_commands": [
                    {"order": 1, "scene": "主播近景"}
                ]
            }
        }


# ==================== Tutor 助教 API ====================

class TutorChatMessage(BaseModel):
    """助教对话历史中的单条消息"""
    role: str = Field(..., description="消息角色: 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class TutorChatRequest(BaseModel):
    """VIP 课后助教聊天请求"""
    user_question: str = Field(..., description="用户问题", min_length=1)
    course_material: str = Field(..., description="当前直播课程讲义上下文")
    chat_history: List[TutorChatMessage] = Field(default_factory=list, description="对话历史")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_question": "如何实现 RAG 知识库？",
                "course_material": "# 课程讲义\n## RAG 概述\n...",
                "chat_history": []
            }
        }


class TutorChatResponse(BaseModel):
    """VIP 课后助教聊天响应"""
    success: bool = Field(..., description="请求是否成功")
    answer: str = Field(..., description="助教回答内容")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "RAG（检索增强生成）是一种..."
            }
        }


# ==================== 商业资产生成 API ====================

class BusinessAssetsRequest(BaseModel):
    """商业资产生成请求"""
    action_queue: List[ActionQueueItem] = Field(..., description="剧本队列")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_queue": [
                    {"type": "text", "content": "大家好..."},
                    {"type": "obs", "scene": "主播近景"}
                ]
            }
        }


class BusinessAssetsResponse(BaseModel):
    """商业资产生成响应"""
    success: bool = Field(..., description="请求是否成功")
    course_material: str = Field(..., description="直播配套课程讲义")
    xiaohongshu: str = Field(..., description="小红书爆款引流文案")
    douyin: str = Field(..., description="抖音短视频分镜脚本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "course_material": "# 课程讲义\n...",
                "xiaohongshu": "💡 90%的程序员不知道...",
                "douyin": "【画面】xxx\n【口播】xxx"
            }
        }


# ==================== 复盘报告 API ====================

class JudgeReportRequest(BaseModel):
    """直播复盘报告生成请求"""
    action_queue: List[ActionQueueItem] = Field(..., description="剧本队列")
    danmu_history: str = Field(default="", description="弹幕互动历史")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_queue": [
                    {"type": "text", "content": "大家好..."}
                ],
                "danmu_history": "观众提问: Cursor 收费吗？"
            }
        }


class JudgeReportResponse(BaseModel):
    """直播复盘报告生成响应"""
    success: bool = Field(..., description="请求是否成功")
    full_report: str = Field(..., description="完整复盘报告")
    radar_scores: Optional[Dict[str, int]] = Field(None, description="雷达图分数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "full_report": "【核心指标雷达】\n极客硬核度得分：85分\n...",
                "radar_scores": {
                    "geek_score": 85,
                    "interaction_score": 78,
                    "commerce_score": 72
                }
            }
        }


# ==================== 通用响应模型 ====================

class ErrorDetail(BaseModel):
    """错误详情"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="当前时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "2.0.0",
                "timestamp": "2026-03-08T12:00:00"
            }
        }
