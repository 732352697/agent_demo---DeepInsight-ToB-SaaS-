"""Agent 系统入口文件。"""

import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tools.tools import search_industry_news


def setup_logging() -> None:
    """初始化全局日志配置。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def create_agent_executor():
    """创建并初始化 Agent 执行器。"""
    load_dotenv()

    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0,
        base_url="https://api.deepseek.com/v1",
    )

    tools = [search_industry_news]

    agent = create_agent(llm, tools)

    return agent


def main() -> None:
    """程序主入口。"""
    setup_logging()
    logging.info("日志系统初始化完成")
    print("Agent 系统初始化成功")

    agent_executor = create_agent_executor()

    result = agent_executor.invoke(
        {
            "messages": [
                ("user", "我要做一份针对大模型产品经理的商业计划，请先帮我查阅一下最新的行业动态，然后总结出 3 个核心趋势。")
            ]
        }
    )

    print("\n" + "=" * 50)
    print("最终输出：")
    print("=" * 50)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
