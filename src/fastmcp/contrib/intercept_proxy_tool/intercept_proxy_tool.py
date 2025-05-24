from collections.abc import Callable
from typing import Annotated, Any

from mcp.types import EmbeddedResource, ImageContent, TextContent
from pydantic import BaseModel, Field

from fastmcp import Context
from fastmcp.client.client import Client
from fastmcp.server.proxy import ProxyTool, _proxy_passthrough
from fastmcp.server.server import FastMCP
from fastmcp.utilities.json_schema import _prune_param

HOOK_PARAMETERS_FIELD_DESCRIPTION = "Additional fields to add to the tool call input schema that will be passed to the hook."
FIELD_DEFAULTS_FIELD_DESCRIPTION = "Default values for args on the tool call."
FIELD_VALUES_FIELD_DESCRIPTION = "Mandatory values for args on the tool call."
PRE_TOOL_CALL_HOOK_FIELD_DESCRIPTION = (
    "A hook that is called before a tool call is made."
)
POST_TOOL_CALL_HOOK_FIELD_DESCRIPTION = (
    "A hook that is called after a tool call is made."
)

HOOK_PARAMETERS_FIELD = Field(
    None,
    description="Additional fields to add to the tool call input schema that will be passed to the hook.",
)

FIELD_DEFAULTS_FIELD = Field(
    default_factory=lambda: {},
    description="Default values for args on the tool call.",
)

FIELD_VALUES_FIELD = Field(
    default_factory=lambda: {},
    description="Mandatory values for args on the tool call.",
)

PRE_TOOL_CALL_HOOK_FIELD = Field(
    None,
    description="A hook that is called before a tool call is made.",
)

POST_TOOL_CALL_HOOK_FIELD = Field(
    None,
    description="A hook that is called after a tool call is made.",
)


class InterceptingProxyTool(ProxyTool):
    """
    A ProxyTool subclass that intercepts the run method to handle redirection.
    """

    extra_fields_schema: dict[str, Any] | None = Field(
        None,
        description="The JSON Schema of the extra fields to add to the tool call input schema, these will be passed to the hook.",
    )

    field_defaults: dict[str, Any] | None = Field(
        None, description=FIELD_DEFAULTS_FIELD_DESCRIPTION
    )

    field_values: dict[str, Any] | None = Field(
        None, description=FIELD_VALUES_FIELD_DESCRIPTION
    )

    pre_tool_call_hook: Callable[[dict[str, Any], Context | None], None] | None = Field(
        None, description=PRE_TOOL_CALL_HOOK_FIELD_DESCRIPTION
    )

    post_tool_call_hook: (
        Callable[
            [list[TextContent | ImageContent | EmbeddedResource], Context | None], None
        ]
        | None
    ) = Field(None, description=POST_TOOL_CALL_HOOK_FIELD_DESCRIPTION)

    def __init__(self, *args, **kwargs):
        super().__init__(fn=_proxy_passthrough, *args, **kwargs)

        self._extra_field_names = []

        if self.extra_fields_schema:
            self._extra_field_names = self.extra_fields_schema.get("properties", {}).keys()
            self.parameters = self.parameters | self.extra_fields_schema

    def add_to_server(self, server: FastMCP):
        server._tool_manager.add_tool(self)

    async def run(
        self, arguments: dict[str, Any], context: Context | None = None
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        hook_args = {}
        if self._extra_field_names and (
            self.pre_tool_call_hook or self.post_tool_call_hook
        ):
            for field in self._extra_field_names:
                hook_args[field] = arguments.pop(field)

        if self.pre_tool_call_hook:
            self.pre_tool_call_hook(hook_args, context)

        tool_args = arguments.copy()

        if self.field_defaults:
            for field, default_value in self.field_defaults.items():
                tool_args[field] = default_value

        if self.field_values:
            for field, mandatory_value in self.field_values.items():
                tool_args[field] = mandatory_value

        response = await super().run(arguments=tool_args, context=context)

        if self.post_tool_call_hook:
            self.post_tool_call_hook(response, context)

        return response

    @classmethod
    def from_proxy_tool(
        cls,
        client: Client,
        proxy_tool: ProxyTool,
        extra_fields_schema: Annotated[
            dict[str, Any] | None, HOOK_PARAMETERS_FIELD_DESCRIPTION
        ] = None,
        field_defaults: Annotated[
            dict[str, Any] | None, FIELD_DEFAULTS_FIELD_DESCRIPTION
        ] = None,
        field_values: Annotated[
            dict[str, Any] | None, FIELD_VALUES_FIELD_DESCRIPTION
        ] = None,
        pre_tool_call_hook: Annotated[
            Callable[[dict[str, Any], Context | None], None] | None,
            PRE_TOOL_CALL_HOOK_FIELD_DESCRIPTION,
        ] = None,
        post_tool_call_hook: Annotated[
            Callable[
                [list[TextContent | ImageContent | EmbeddedResource], Context | None],
                None,
            ]
            | None,
            POST_TOOL_CALL_HOOK_FIELD_DESCRIPTION,
        ] = None,
    ) -> "InterceptingProxyTool":
        return cls(
            client=client,
            name=proxy_tool.name,
            description=proxy_tool.description,
            parameters=proxy_tool.parameters,
            extra_fields_schema=extra_fields_schema,
            field_defaults=field_defaults,
            field_values=field_values,
            pre_tool_call_hook=pre_tool_call_hook,
            post_tool_call_hook=post_tool_call_hook,
        )
