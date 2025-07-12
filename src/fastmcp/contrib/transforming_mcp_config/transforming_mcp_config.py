from typing import Any

from pydantic import Field

from fastmcp import FastMCP
from fastmcp.client.transports import ClientTransport, FastMCPTransport
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer, StdioMCPServer
from fastmcp.tools.tool_transform import (
    ToolTransformRequest,
)
from fastmcp.utilities.types import FastMCPBaseModel

# class ArgTransformRequest(FastMCPBaseModel):
#     """A model for requesting a single argument transform."""

#     model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, use_attribute_docstrings=True, extra="forbid")

#     name: str | None = Field(default=None)
#     description: str | None = Field(default=None)
#     default: str | int | float | bool | None = Field(default=None)
#     hide: bool = Field(default=False)
#     required: Literal[True] | None = Field(default=None)
#     examples: Any | None = Field(default=None)

#     def to_arg_transform(self) -> ArgTransform:
#         """Convert the argument transform to a FastMCP argument transform."""
#         return ArgTransform(**self.model_dump(exclude_none=True))  # pyright: ignore[reportAny]

# class ToolTransformRequest(FastMCPComponent):
#     """Provides a way to transform a tool."""

#     name: str | None = Field(default=None)

#     model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True, use_attribute_docstrings=True, extra="forbid")

#     arguments: dict[str, ArgTransformRequest] = Field(default_factory=dict)
#     """A dictionary of argument transforms to apply to the tool."""

#     def apply(self, tool: FastMCPTool) -> FastMCPTool:
#         """Apply the transform to the tool."""

#         return TransformedTool.from_tool(
#             tool=tool,
#             **self.model_dump(exclude_none=True, exclude={"arguments"}),
#             transform_args={k: v.to_arg_transform() for k, v in self.arguments.items()},
#         )

# async def apply_to_server(self, server: FastMCP, tool_name: str):

#     existing_tool = await server.get_tool(tool_name)

#     if existing_tool is None:
#         raise ValueError(f"Tool {tool_name} does not exist in the server.")

#     server.remove_tool(tool_name)

#     server.add_tool(self.apply_to_tool(existing_tool))


# class MultiToolTransform(FastMCPBaseModel):
#     """A configuration for a tool allowlist and transformations."""

#     allowed: list[str] | None = Field(default=None)
#     """The tools that are allowed to be used."""

#     blocked: list[str] | None = Field(default=None)
#     """The tools that are blocked from being used."""

#     extra: list[SimpleToolTypes] = Field(default_factory=list)
#     """Any extra tools to be inserted into the tool manager."""

#     transformations: dict[str, SingleToolTransform] = Field(default_factory=dict)
#     """The transformations to apply to the tools."""

#     def tool_passes_filter(self, tool_name: str) -> bool:
#         """Check if the tool name matches the allowlist."""

#         return (self.allowed is None or tool_name in self.allowed) and (self.blocked is None or tool_name not in self.blocked)

#     def apply(self, source_tools: dict[str, FastMCPTool]) -> dict[str, FastMCPTool]:
#         """Apply the tool configuration to the source tools."""

#         filtered_tools: dict[str, FastMCPTool] = {
#             tool_name: tool for tool_name, tool in source_tools.items() if self.tool_passes_filter(tool.name)
#         } | {tool.name: tool.to_tool() for tool in self.extra}

#         for tool_name, transform in self.transformations.items():
#             if tool_name not in filtered_tools:
#                 msg = f"Requested a transformation for tool {tool_name} that is not in the source tools."
#                 raise ValueError(msg)

#             if transformed_tool := transform.apply_to_tool(filtered_tools[tool_name]):
#                 filtered_tools[tool_name] = transformed_tool

#         return filtered_tools


class WrappedMCPServerMixin(FastMCPBaseModel):
    """A mixin that enables wrapping an MCP Server (Or a FastMCP Agents Server) with tool transforms."""

    tools: dict[str, ToolTransformRequest] = Field(default_factory=dict)
    """The multi-tool transform to apply to the tools."""

    def to_transport(self) -> FastMCPTransport:
        """Get the transport for the server."""

        transport: ClientTransport = super().to_transport()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]

        wrapped_mcp_server = FastMCP.as_proxy(transport)

        [
            wrapped_mcp_server.add_tool_transform(name, transform)
            for name, transform in self.tools.items()
        ]

        return FastMCPTransport(wrapped_mcp_server)

    # def as_proxy(self) -> TransformingFastMCPProxy:
    #     """Get the transport for the server."""

    #     if not hasattr(self, "to_transport"):
    #         msg: str = f"to_transport is not implemented for {self.__class__.__name__}"
    #         raise NotImplementedError(msg)

    #     transport: ClientTransport = super().to_transport()  #pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]

    #     return TransformingFastMCPProxy(
    #         name=self.name,
    #         client=Client(transport=transport),
    #         multi_tool_transform=self.tools,
    #     )

    # @asynccontextmanager
    # async def as_transforming_proxy(self) -> AsyncGenerator[FastMCPProxy, None]:
    #     """Activate the transforming proxy server."""

    #     transport: ClientTransport = self.to_transport()
    #     client: Client[ClientTransport] | None = None

    #     try:
    #         client = Client(transport=transport, init_timeout=DEFAULT_INIT_TIMEOUT)

    #         async with client:
    #             _ = await client.ping()

    #             mcp_server = FastMCP.as_proxy(client)

    #             tools: dict[str, FastMCPTool] = await mcp_server.get_tools()

    #             for tool_name, tool in tools.items():
    #                 if tool_name in self.tools.transformations:
    #                     _ = self.tools.transformations.pop(tool_name)

    #             self.tools.transformations.update(tools)

    #             proxy: TransformingFastMCPProxy = TransformingFastMCPProxy(
    #                 name=self.name,
    #                 client=client,
    #                 multi_tool_transform=self.tools,
    #             )

    #             yield proxy

    #     finally:
    #         if client:
    #             await client.close()


class TransformingStdioMCPServer(WrappedMCPServerMixin, StdioMCPServer):
    """A Stdio server with tool transforms."""


class TransformingRemoteMCPServer(WrappedMCPServerMixin, RemoteMCPServer):
    """A Remote server with tool transforms."""


class TransformingMCPConfig(MCPConfig):
    """A MCP Config with tool transforms."""

    mcpServers: dict[str, TransformingStdioMCPServer | TransformingRemoteMCPServer] = (
        Field(default_factory=dict)
    )
    """The MCP servers."""

    @classmethod
    def _validate_stdio_server(
        cls, server_config: dict[str, Any]
    ) -> TransformingStdioMCPServer:
        """Validate a stdio server configuration."""
        return TransformingStdioMCPServer.model_validate(server_config)

    @classmethod
    def _validate_remote_server(
        cls, server_config: dict[str, Any]
    ) -> TransformingRemoteMCPServer:
        """Validate a remote server configuration."""
        return TransformingRemoteMCPServer.model_validate(server_config)


# class MCPConfigTransport(FastMCPConfigTransport):

#     def __init__(self, config: MCPConfig | dict):

#         raise NotImplementedError("Not implemented")


# MCPServerConfigTypes = StdioMCPServerConfig | RemoteMCPServerConfig
