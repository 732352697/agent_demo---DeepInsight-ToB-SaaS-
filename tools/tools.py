"""Industry analysis tools for the Agent system."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    """Input schema for industry news search requests."""

    query: str = Field(
        ...,
        description=(
            "A focused industry-news search query. It should clearly specify the target "
            "domain, topic, company, technology, geography, and (optionally) time range. "
            "Examples: 'AI Agent funding trends in 2025', 'latest open-source LLM releases "
            "for enterprise in China', 'regulatory updates for generative AI in EU'."
        ),
        min_length=2,
    )


@tool(args_schema=SearchInput)
def search_industry_news(query: str) -> str:
    """Search and summarize recent industry news for a given topic.

    This tool is designed to provide fast, high-level industry updates when the Agent
    needs market context, trend signals, ecosystem movement, or recent developments.
    The output is a simulated news summary in this MVP stage.

    When you should call this tool:
    - The user asks for latest industry dynamics, recent news, market trends, or
      ecosystem updates.
    - The user needs directional signals before deeper analysis.
    - The task requires external-looking context (e.g., competition, financing,
      product launches, policy, partnerships).

    When you should NOT call this tool:
    - The question is purely mathematical, coding-only, or unrelated to industry
      developments.
    - You already have sufficient context in conversation and no incremental
      external-style update is needed.

    How to construct the `query` argument:
    - Keep it specific and scoped instead of generic.
    - Include core subject + angle + optional region/time constraints.
    - Good examples:
      1) "AI Agent platform product launches in Q1 2026"
      2) "enterprise adoption trends of multimodal LLMs in healthcare"
      3) "open-source vs closed-source LLM competition in APAC"
    - Avoid vague inputs like "AI news" unless the user explicitly asks broad updates.

    Returns:
        A concise, synthetic industry-news digest string for downstream reasoning.
    """
    print(f"[System: 正在调用 search_industry_news 工具查询 '{query}'...]")

    return (
        "[模拟行业快讯] 2026年第一季度，AI Agent 赛道出现三大趋势："
        "其一，多家云厂商发布面向企业流程自动化的 Agent 编排平台；"
        "其二，头部大模型厂商推出更低延迟的推理版本，推动实时 Agent 应用落地；"
        "其三，金融与制造行业加速试点‘多 Agent 协作 + 私有知识库’方案，"
        "重点关注可审计性、稳定性与成本控制。"
    )
