from typing import Any, Literal, Protocol, overload

from mcp.types import (
    ContentBlock,
    ModelPreferences,
    SamplingMessage,
)
from pydantic import BaseModel

from fastmcp.tools import Tool


class SamplingProtocol(Protocol):
    async def __call__(
        self,
        messages: str | list[str | SamplingMessage],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model_preferences: ModelPreferences | str | list[str] | None = None,
    ) -> ContentBlock: ...


CompletionMessage = dict[str, Any] | BaseModel
CompletionMessages = list[CompletionMessage]

FastMCPToolCall = tuple[Tool, dict[str, Any]]


class LLMCompletionsProtocol(Protocol):
    @overload
    async def text(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        response_type: Literal["mcp"] = "mcp",
        **kwargs: Any,
    ) -> ContentBlock: ...

    @overload
    async def text(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        response_type: Literal["raw"],
        **kwargs: Any,
    ) -> CompletionMessage: ...

    async def text(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        response_type: Literal["mcp", "raw"] = "mcp",
        **kwargs: Any,
    ) -> CompletionMessage | ContentBlock: ...

    """Performs a text completion using the configured LLM.

    Args:
        system_prompt: The system prompt to use for the completion.
        messages: The messages to use for the completion.
        response_type: The type of response to return: A ContentBlock if "mcp", a raw CompletionMessage if "raw".
        **kwargs: Additional keyword arguments to pass to the completion.
    """

    @overload
    async def tools(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        tools: list[Tool] | dict[str, Tool],
        parallel_tool_calls: Literal[True] = True,
        response_type: Literal["fastmcp"] = "fastmcp",
        **kwargs: Any,
    ) -> list[FastMCPToolCall]: ...

    @overload
    async def tools(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        tools: list[Tool] | dict[str, Tool],
        parallel_tool_calls: Literal[False] = False,
        response_type: Literal["fastmcp"] = "fastmcp",
        **kwargs: Any,
    ) -> FastMCPToolCall: ...

    @overload
    async def tools(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        tools: list[Tool] | dict[str, Tool],
        parallel_tool_calls: Literal[False] = False,
        response_type: Literal["raw"] = "raw",
        **kwargs: Any,
    ) -> CompletionMessage: ...

    async def tools(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        tools: list[Tool] | dict[str, Tool],
        parallel_tool_calls: bool = False,
        response_type: Literal["raw", "fastmcp"] = "fastmcp",
        **kwargs: Any,
    ) -> CompletionMessage | list[FastMCPToolCall] | FastMCPToolCall: ...

    """Picks tools to call based on the system prompt and messages.

    Args:
        system_prompt: The system prompt to use for the tool picking.
        messages: The messages to use for the tool picking.
        tools: The tools to pick from.
        parallel_tool_calls: Whether to call tools in parallel.
        response_type: The type of response to return: A list of FastMCP Tools with call arguments if "fastmcp", a raw CompletionMessage if "raw".
        **kwargs: Additional keyword arguments to pass to the tool picking.
    """

    @staticmethod
    async def call_tool(
        fastmcp_tool_call: FastMCPToolCall,
    ) -> list[ContentBlock]:
        tool, arguments = fastmcp_tool_call

        tool_call_result = await tool.run(arguments)

        return tool_call_result.content
