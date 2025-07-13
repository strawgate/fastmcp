"""Canonical MCP Configuration Format.

This module defines the standard configuration format for Model Context Protocol (MCP) servers.
It provides a client-agnostic, extensible format that can be used across all MCP implementations.

The configuration format supports both stdio and remote (HTTP/SSE) transports, with comprehensive
field definitions for server metadata, authentication, and execution parameters.

Example configuration:
    {
        "mcpServers": {
            "my-server": {
                "command": "npx",
                "args": ["-y", "@my/mcp-server"],
                "env": {"API_KEY": "secret"},
                "timeout": 30000,
                "description": "My MCP server"
            }
        }
    }
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal
from urllib.parse import urlparse

import httpx
from pydantic import AnyUrl, BaseModel, ConfigDict, Field
from pydantic.type_adapter import TypeAdapter

from fastmcp.tools.tool_transform import ToolTransformConfig
from fastmcp.utilities.types import FastMCPBaseModel

if TYPE_CHECKING:
    from fastmcp.client.transports import (
        ClientTransport,
        FastMCPTransport,
        SSETransport,
        StdioTransport,
        StreamableHttpTransport,
    )


def infer_transport_type_from_url(
    url: str | AnyUrl,
) -> Literal["http", "sse"]:
    """
    Infer the appropriate transport type from the given URL.
    """
    url = str(url)
    if not url.startswith("http"):
        raise ValueError(f"Invalid URL: {url}")

    parsed_url = urlparse(url)
    path = parsed_url.path

    # Match /sse followed by /, ?, &, or end of string
    if re.search(r"/sse(/|\?|&|$)", path):
        return "sse"
    else:
        return "http"


class WrappedMCPServerMixin(FastMCPBaseModel):
    """A mixin that enables wrapping an MCP Server with tool transforms."""

    tools: dict[str, ToolTransformConfig] = Field(default_factory=dict)
    """The multi-tool transform to apply to the tools."""

    def to_transport(self) -> FastMCPTransport:
        """Get the transport for the server."""

        from fastmcp.client.transports import FastMCPTransport
        from fastmcp.server.server import FastMCP

        transport: ClientTransport = super().to_transport()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]

        wrapped_mcp_server = FastMCP.as_proxy(
            transport, tool_transformations=self.tools
        )

        return FastMCPTransport(wrapped_mcp_server)


class StdioMCPServer(BaseModel):
    """MCP server configuration for stdio transport.

    This is the canonical configuration format for MCP servers using stdio transport.
    """

    # Required fields
    command: str

    # Common optional fields
    args: list[str] = Field(default_factory=list)
    env: dict[str, Any] = Field(default_factory=dict)

    # Transport specification
    transport: Literal["stdio"] = "stdio"
    type: Literal["stdio"] | None = None  # Alternative transport field name

    # Execution context
    cwd: str | None = None  # Working directory for command execution
    timeout: int | None = None  # Maximum response time in milliseconds

    # Metadata
    description: str | None = None  # Human-readable server description
    icon: str | None = None  # Icon path or URL for UI display

    # Authentication configuration
    authentication: dict[str, Any] | None = None  # Auth configuration object

    model_config = ConfigDict(extra="allow")  # Preserve unknown fields

    def to_transport(self) -> StdioTransport:
        from fastmcp.client.transports import StdioTransport

        return StdioTransport(
            command=self.command,
            args=self.args,
            env=self.env,
            cwd=self.cwd,
        )


class TransformingStdioMCPServer(WrappedMCPServerMixin, StdioMCPServer):
    """A Stdio server with tool transforms."""


class RemoteMCPServer(BaseModel):
    """MCP server configuration for HTTP/SSE transport.

    This is the canonical configuration format for MCP servers using remote transports.
    """

    # Required fields
    url: str

    # Transport configuration
    transport: Literal["http", "streamable-http", "sse"] | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    # Authentication
    auth: Annotated[
        str | Literal["oauth"] | httpx.Auth | None,
        Field(
            description='Either a string representing a Bearer token, the literal "oauth" to use OAuth authentication, or an httpx.Auth instance for custom authentication.',
        ),
    ] = None

    # Timeout configuration
    sse_read_timeout: datetime.timedelta | int | float | None = None
    timeout: int | None = None  # Maximum response time in milliseconds

    # Metadata
    description: str | None = None  # Human-readable server description
    icon: str | None = None  # Icon path or URL for UI display

    # Authentication configuration
    authentication: dict[str, Any] | None = None  # Auth configuration object

    model_config = ConfigDict(
        extra="allow", arbitrary_types_allowed=True
    )  # Preserve unknown fields

    def to_transport(self) -> StreamableHttpTransport | SSETransport:
        from fastmcp.client.transports import SSETransport, StreamableHttpTransport

        if self.transport is None:
            transport = infer_transport_type_from_url(self.url)
        else:
            transport = self.transport

        if transport == "sse":
            return SSETransport(
                self.url,
                headers=self.headers,
                auth=self.auth,
                sse_read_timeout=self.sse_read_timeout,
            )
        else:
            # Both "http" and "streamable-http" map to StreamableHttpTransport
            return StreamableHttpTransport(
                self.url,
                headers=self.headers,
                auth=self.auth,
                sse_read_timeout=self.sse_read_timeout,
            )


class TransformingRemoteMCPServer(WrappedMCPServerMixin, RemoteMCPServer):
    """A Remote server with tool transforms."""


MCPServerTypes = (
    StdioMCPServer
    | TransformingStdioMCPServer
    | RemoteMCPServer
    | TransformingRemoteMCPServer
)

McpServersType = dict[str, MCPServerTypes]


class MCPConfig(BaseModel):
    """Canonical MCP configuration format.

    This defines the standard configuration format for Model Context Protocol servers.
    The format is designed to be client-agnostic and extensible for future use cases.
    """

    mcpServers: McpServersType

    model_config = ConfigDict(extra="allow")  # Preserve unknown top-level fields

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> MCPConfig:
        """Parse MCP configuration from dictionary format."""

        type_adapter = TypeAdapter(McpServersType | MCPConfig)

        # Allow deserializing a config that has the contents of McpServers at the top-level
        result: McpServersType | MCPConfig = type_adapter.validate_python(config)

        return result if isinstance(result, MCPConfig) else cls(mcpServers=result)

    def to_dict(self) -> dict[str, Any]:
        """Convert MCPConfig to dictionary format, preserving all fields."""
        return self.model_dump(exclude_none=True, serialize_as_any=True)

    def write_to_file(self, file_path: Path) -> None:
        """Write configuration to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_file(cls, file_path: Path) -> MCPConfig:
        """Load configuration from JSON file."""
        if not file_path.exists():
            return cls(mcpServers={})
        if not (content := file_path.read_text().strip()):
            return cls(mcpServers={})
        data = json.loads(content)
        return cls.from_dict(data)

    def add_server(self, name: str, server: MCPServerTypes) -> None:
        """Add or update a server in the configuration."""
        self.mcpServers[name] = server

    def remove_server(self, name: str) -> None:
        """Remove a server from the configuration."""
        if name in self.mcpServers:
            del self.mcpServers[name]


def update_config_file(
    file_path: Path,
    server_name: str,
    server_config: MCPServerTypes,
) -> None:
    """Update MCP configuration file with new server, preserving existing fields."""
    config = MCPConfig.from_file(file_path)

    # If updating an existing server, merge with existing configuration
    # to preserve any unknown fields
    if server_name in config.mcpServers:
        existing_server = config.mcpServers[server_name]
        # Get the raw dict representation of both servers
        existing_dict = existing_server.model_dump()
        new_dict = server_config.model_dump(exclude_none=True)

        # Merge, with new values taking precedence
        merged_dict = {**existing_dict, **new_dict}

        # Create new server instance with merged data
        if "command" in merged_dict:
            merged_server = StdioMCPServer.model_validate(merged_dict)
        else:
            merged_server = RemoteMCPServer.model_validate(merged_dict)

        config.add_server(server_name, merged_server)
    else:
        config.add_server(server_name, server_config)

    config.write_to_file(file_path)
