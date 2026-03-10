"""Background worker for News Reporter Agent."""

import logging
import time
import asyncio
from datetime import datetime
from src.subagents import SubagentExecutor, get_subagent_config
from src.tools import get_available_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news-reporter-worker")

def run_news_reporter():
    """Trigger the news-reporter subagent to process inbox."""
    logger.info("Starting hourly news-reporting task...")
    
    config = get_subagent_config("news-reporter")
    if not config:
        logger.error("Could not find configuration for 'news-reporter' subagent.")
        return

    # Tools are inherited or specific
    tools = get_available_tools(subagent_enabled=False)
    
    executor = SubagentExecutor(
        config=config,
        tools=tools,
        thread_id="news-reporter-system-thread", # Static thread for background tasks
    )
    
    prompt = "请执行你的常规任务：巡检 inbox.md 并执行深度清洗 (cleansing_fetch) 入库。"
    
    try:
        # executor.execute is synchronous (it internal calls asyncio.run)
        result = executor.execute(prompt)
        logger.info(f"Task completed successfully: {result.result[:100] if result.result else 'No result'}...")
    except Exception as e:
        logger.error(f"Error during news-reporting task: {e}")

def main():
    logger.info("News Reporter Background Worker started.")
    while True:
        try:
            run_news_reporter()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        logger.info("Sleeping for 1 hour...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
