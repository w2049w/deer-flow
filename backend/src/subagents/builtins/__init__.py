"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .general_purpose import GENERAL_PURPOSE_CONFIG
from .news_reporter import NEWS_REPORTER_CONFIG
from .news_editor import NEWS_EDITOR_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "NEWS_REPORTER_CONFIG",
    "NEWS_EDITOR_CONFIG",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    "news-reporter": NEWS_REPORTER_CONFIG,
    "news-editor": NEWS_EDITOR_CONFIG,
}
