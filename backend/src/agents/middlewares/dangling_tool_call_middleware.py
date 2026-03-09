"""Middleware to fix dangling tool calls in message history.

A dangling tool call occurs when an AIMessage contains tool_calls but there are
no corresponding ToolMessages in the history (e.g., due to user interruption or
request cancellation). This causes LLM errors due to incomplete message format.

This middleware intercepts the model call to detect and patch such gaps by
inserting synthetic ToolMessages with an error indicator immediately after the
AIMessage that made the tool calls, ensuring correct message ordering.

Note: Uses wrap_model_call instead of before_model to ensure patches are inserted
at the correct positions (immediately after each dangling AIMessage), not appended
to the end of the message list as before_model + add_messages reducer would do.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, ToolMessage

logger = logging.getLogger(__name__)


class DanglingToolCallMiddleware(AgentMiddleware[AgentState]):
    """Inserts placeholder ToolMessages for dangling tool calls before model invocation.

    Scans the message history for AIMessages whose tool_calls lack corresponding
    ToolMessages, and injects synthetic error responses immediately after the
    offending AIMessage so the LLM receives a well-formed conversation.
    """

    def _build_patched_messages(self, messages: list) -> list:
        """Surgically fix missing tool call names and prevent validation errors."""
        patch_count = 0
        name_fixed_count = 0
        
        # 1. Identify existing tool responses
        existing_tool_ids = {
            getattr(m, "tool_call_id", None) 
            for m in messages 
            if getattr(m, "type", None) == "tool" or isinstance(m, ToolMessage)
        }
        existing_tool_ids.discard(None)

        patched_messages = []
        for i, msg in enumerate(messages):
            # A. Fix AI messages
            if getattr(msg, "type", None) == "ai" or isinstance(msg, AIMessage):
                tcs = getattr(msg, "tool_calls", None) or []
                fixed_tcs = []
                msg_fixed = False
                for tc in tcs:
                    if isinstance(tc, dict):
                        new_tc = tc.copy()
                        if not new_tc.get("name"): # Catch None, empty string, etc.
                            new_tc["name"] = "unknown_tool"
                            msg_fixed = True
                            name_fixed_count += 1
                        fixed_tcs.append(new_tc)
                    else:
                        fixed_tcs.append(tc)
                
                # Always rebuild to be safe from hidden malformed fields in additional_kwargs
                new_msg = AIMessage(
                    content=msg.content,
                    tool_calls=fixed_tcs,
                )
                if hasattr(msg, "id"):
                    new_msg.id = msg.id
                msg = new_msg
                if msg_fixed:
                    logger.info(f"DanglingToolCallMiddleware: fixed AI message at index {i}")

            patched_messages.append(msg)

            # B. Inject placeholder for dangling calls
            if getattr(msg, "type", None) == "ai":
                for tc in getattr(msg, "tool_calls", None) or []:
                    tid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    if tid and tid not in existing_tool_ids:
                        target_name = "unknown_tool"
                        if isinstance(tc, dict):
                            target_name = tc.get("name") or "unknown_tool"
                        
                        patched_messages.append(
                            ToolMessage(
                                content="[Tool call interrupted]",
                                tool_call_id=tid,
                                name=target_name,
                                status="error"
                            )
                        )
                        existing_tool_ids.add(tid)
                        patch_count += 1

        if patch_count > 0 or name_fixed_count > 0:
            logger.info(f"DanglingToolCallMiddleware SUMMARY: patched {patch_count} responses, fixed {name_fixed_count} AI names")
        
        return patched_messages

    @override
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        patched = self._build_patched_messages(request.messages)
        if patched is not None:
            request = request.override(messages=patched)
        return handler(request)

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        patched = self._build_patched_messages(request.messages)
        if patched is not None:
            request = request.override(messages=patched)
        return await handler(request)
