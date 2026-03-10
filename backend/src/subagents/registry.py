"""Subagent registry for managing available subagents."""

import logging
import re
from dataclasses import replace
from typing import Any

from src.config.agents_config import list_custom_agents, load_agent_config, load_agent_soul
from src.subagents.builtins import BUILTIN_SUBAGENTS
from src.subagents.config import SubagentConfig

logger = logging.getLogger(__name__)


def get_subagent_config(name: str) -> SubagentConfig | None:
    """Get a subagent configuration by name or alias.

    Args:
        name: The name or alias of the subagent.

    Returns:
        SubagentConfig if found, None otherwise.
    """
    # 1. Direct name match in BUILTIN_SUBAGENTS
    config = BUILTIN_SUBAGENTS.get(name)

    # 2. Alias match in BUILTIN_SUBAGENTS
    if config is None:
        for builtin_cfg in BUILTIN_SUBAGENTS.values():
            if name in builtin_cfg.aliases:
                config = builtin_cfg
                break

    if config is None:
        # 3. Check if it's a custom agent (by name first)
        try:
            agent_cfg = load_agent_config(name)
            if agent_cfg:
                config = _create_config_from_agent(name, agent_cfg)
        except Exception:
            pass

    # 4. Check if any custom agent matches by alias
    if config is None:
        try:
            for agent_cfg in list_custom_agents():
                if name in agent_cfg.aliases:
                    config = _create_config_from_agent(agent_cfg.name, agent_cfg)
                    break
        except Exception:
            pass

    if config is None:
        return None

    # Apply timeout override from config.yaml (lazy import to avoid circular deps)
    from src.config.subagents_config import get_subagents_app_config

    app_config = get_subagents_app_config()
    effective_timeout = app_config.get_timeout_for(name)
    if effective_timeout != config.timeout_seconds:
        logger.debug(f"Subagent '{name}': timeout overridden by config.yaml ({config.timeout_seconds}s -> {effective_timeout}s)")
        config = replace(config, timeout_seconds=effective_timeout)

    return config


def list_subagents() -> list[SubagentConfig]:
    """List all available subagent configurations.

    Returns:
        List of all registered SubagentConfig instances.
    """
    builtin_names = list(BUILTIN_SUBAGENTS.keys())
    custom_names = [agent.name for agent in list_custom_agents()]

    all_configs = []
    for name in builtin_names + custom_names:
        cfg = get_subagent_config(name)
        if cfg:
            all_configs.append(cfg)
    return all_configs


def get_subagent_names() -> list[str]:
    """Get all available subagent names.

    Returns:
        List of subagent names.
    """
    builtin_names = list(BUILTIN_SUBAGENTS.keys())
    custom_names = [agent.name for agent in list_custom_agents()]
    return builtin_names + custom_names


def find_best_subagent(task_prompt: str) -> SubagentConfig | None:
    """Find the most suitable subagent for a given task using expertise matching.

    Initial implementation uses keyword/tag overlap. Can be upgraded to embeddings later.

    Args:
        task_prompt: The task description for the subagent.

    Returns:
        The best SubagentConfig found, or None.
    """
    subagents = list_subagents()
    if not subagents:
        return None

    prompt_low = task_prompt.lower()
    scores: list[tuple[float, SubagentConfig]] = []

    for sa in subagents:
        score = 0.0
        # 1. Direct name match (highest weight)
        if sa.name.lower() in prompt_low:
            score += 2.0

        # 2. Expertise tag match (medium weight)
        for tag in sa.expertise:
            if tag.lower() in prompt_low:
                score += 1.5
            # Sub-tag/Keyword match
            for word in tag.lower().split():
                if len(word) > 3 and word in prompt_low:
                    score += 0.5

        # 3. Description match (low weight)
        desc_words = re.findall(r'\w+', sa.description.lower())
        for word in desc_words:
            if len(word) > 4 and word in prompt_low:
                score += 0.1

        # 4. Alias match (high weight)
        for alias in sa.aliases:
            if alias.lower() in prompt_low:
                score += 2.0

        if score > 0:
            scores.append((score, sa))

    if not scores:
        # Fallback: Prefer general-purpose if no specific match
        for sa in subagents:
            if sa.name == "general-purpose":
                return sa
        return subagents[0] if subagents else None

    # Sort by score descending
    scores.sort(key=lambda x: x[0], reverse=True)
    best_score, best_sa = scores[0]

    logger.info(f"Subagent search for '{task_prompt[:50]}...': found {best_sa.name} with score {best_score}")
    return best_sa


def _create_config_from_agent(name: str, agent_cfg: Any) -> SubagentConfig:
    """Helper to create SubagentConfig from AgentConfig."""
    soul = load_agent_soul(name) or ""
    system_prompt = f"""You are {name}, a specialized subagent.
Your goal is to complete the tasks delegated to you by the lead agent.

<agent_identity>
Name: {name}
Description: {agent_cfg.description or "A specialized agent."}
</agent_identity>

<soul>
{soul}
</soul>

<guidelines>
- Focus on completing the delegated task efficiently
- Use available tools as needed to accomplish the goal
- Think step by step but act decisively
- If you encounter issues, explain them clearly in your response
- Return a concise summary of what you accomplished
- Do NOT ask for clarification - work with the information provided
</guidelines>

<working_directory>
You have access to the same sandbox environment as the parent agent:
- User uploads: `/mnt/user-data/uploads`
- User workspace: `/mnt/user-data/workspace`
- Output files: `/mnt/user-data/outputs`
</working_directory>
"""
    return SubagentConfig(
        name=name,
        description=agent_cfg.description,
        system_prompt=system_prompt,
        expertise=agent_cfg.expertise,
        aliases=agent_cfg.aliases,
        tools=None,
        model=agent_cfg.model or "inherit",
    )
