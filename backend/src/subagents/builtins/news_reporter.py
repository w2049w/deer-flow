"""News Reporter subagent configuration."""

from src.subagents.config import SubagentConfig

NEWS_REPORTER_CONFIG = SubagentConfig(
    name="news-reporter",
    description="""顶级信息采集与清洗专家。
    擅长将散乱的 URL 转化为清洁的 Markdown 格式并存入数据库。
    """,
    expertise=["记者", "信息提取", "数据管理", "内容清洗"],
    system_prompt="""您是“数字员工：记者”。
您的使命：接收 URL，入库清洗。

### 极简 SOP：
1. **录入并清洗**：当有新 URL 时，使用 `add_to_inbox` 录入，再用 `cleansing_fetch` 完成清洗。
2. **主动巡检**：若无新 URL，直接使用 `cleansing_fetch` 处理 `inbox.md` 中已有的待处理项。
3. **结束**：简要报告结果（已处理数量/新录入数量）。
""",
    # 极简工具集
    tools=[
        "my-daily-news-service__add_to_inbox",
        "my-daily-news-service__cleansing_fetch"
    ],
    disallowed_tools=["swallow_inbox", "task", "ask_clarification", "fetch_news", "list_db_stats"],
    model="minimax-m2.5",
    max_turns=5,
)
