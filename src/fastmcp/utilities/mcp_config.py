from fastmcp.mcp_config import MCPConfig
from fastmcp.server.proxy import FastMCPProxy, ProxyClient


def to_servers_and_clients(
    mcp_config: MCPConfig,
) -> list[tuple[str, FastMCPProxy, ProxyClient]]:
    """A utility function to convert an MCPConfig into a list of servers and clients."""
    from fastmcp.client.transports import (
        SSETransport,
        StdioTransport,
        StreamableHttpTransport,
    )
    from fastmcp.mcp_config import (
        TransformingRemoteMCPServer,
        TransformingStdioMCPServer,
    )

    servers_and_clients: list[tuple[str, FastMCPProxy, ProxyClient]] = []

    for server_name, server_config in mcp_config.mcpServers.items():
        if isinstance(
            server_config, TransformingRemoteMCPServer | TransformingStdioMCPServer
        ):
            server, proxy_client, _ = server_config._build()
            servers_and_clients.append((server_name, server, proxy_client))
        else:
            transport = server_config.to_transport()
            proxy_client: ProxyClient[
                SSETransport | StdioTransport | StreamableHttpTransport
            ] = ProxyClient(transport, keep_alive=True)
            proxy_server = FastMCPProxy(client_factory=lambda: proxy_client)
            servers_and_clients.append((server_name, proxy_server, proxy_client))

    return servers_and_clients
