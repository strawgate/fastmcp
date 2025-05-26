from typing import Any, Literal, Protocol

from mcp.types import EmbeddedResource, ImageContent, TextContent

from fastmcp.contrib.tool_transformer.base import (
    BaseExtraToolParameter,
    BaseToolParameterOverride,
)


class ExtraParameterNumber(BaseExtraToolParameter):
    """An extra parameter that is a number."""

    type: Literal["number"] = "number"
    default: int | float | None = None


class ExtraParameterString(BaseExtraToolParameter):
    """An extra parameter that is a string."""

    type: Literal["string"] = "string"
    default: str | None = None


class ExtraParameterBoolean(BaseExtraToolParameter):
    """An extra parameter that is a boolean."""

    type: Literal["boolean"] = "boolean"
    default: bool | None = None


ExtraToolParameterTypes = (
    ExtraParameterBoolean | ExtraParameterString | ExtraParameterNumber
)


class PostToolCallHookProtocol(Protocol):
    async def __call__(
        self,
        response: list[TextContent | ImageContent | EmbeddedResource],
        tool_args: dict[str, Any],
        hook_args: dict[str, Any],
    ) -> None: ...


class PreToolCallHookProtocol(Protocol):
    async def __call__(
        self,
        tool_args: dict[str, Any],
        hook_args: dict[str, Any],
    ) -> None: ...


class ToolParameterOverride(BaseToolParameterOverride):
    """A parameter override for a tool."""
