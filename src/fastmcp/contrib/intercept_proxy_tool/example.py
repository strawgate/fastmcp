"""Sample code for FastMCP using InterceptingProxyTool."""

import asyncio
from typing import Any

from mcp.types import EmbeddedResource, ImageContent, TextContent
from pydantic import BaseModel, Field

from fastmcp import Context, FastMCP
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.contrib.intercept_proxy_tool import InterceptingProxyTool
from fastmcp.server.proxy import ProxyTool
from fastmcp.tools.tool import Tool as FastMCPTool


# Define a simple backend tool
class BackendTool:
    async def run(
        self, text: str, count: int = 1, prefix: str = ""
    ) -> list[TextContent]:
        """Echo the input text a specified number of times with an optional prefix."""
        return [TextContent(text=f"{prefix}{text}" * count, type="text")]


# Define a second backend tool
class SecondBackendTool:
    async def run(
        self, text: str, count: int = 1, prefix: str = ""
    ) -> list[TextContent]:
        """Echo the input text a specified number of times with an optional prefix."""
        return [TextContent(text=f"{prefix}{text}" * count, type="text")]


# Implement pre and post hooks
def pre_hook(arguments: dict[str, Any], context: Context | None) -> None:
    """Example pre-tool call hook."""
    print(f"Pre-hook called with arguments: {arguments}")
    # Example: Modify arguments (though typically done via field_defaults/values)
    # arguments["extra_info"] = "added_by_pre_hook"


def post_hook(
    response: list[TextContent | ImageContent | EmbeddedResource],
    context: Context | None,
) -> None:
    """Example post-tool call hook."""
    print(f"Post-hook called with response: {response}")
    # Example: Process response
    # if response and isinstance(response[0], TextContent):
    #     response[0].text = f"Processed: {response[0].text}"


async def main():
    # 1. Set up the backend server
    backend_server = FastMCP("BackendServer")

    backend_tool_instance = BackendTool()
    backend_server.add_tool(backend_tool_instance.run, name="first_echo_tool")

    second_backend_tool_instance = SecondBackendTool()
    backend_server.add_tool(second_backend_tool_instance.run, name="second_echo_tool")

    # 2. Create a client for the backend server
    backend_client = Client(transport=FastMCPTransport(backend_server))

    # 3. Set up the proxy and frontend server
    proxy_server = FastMCP.as_proxy(backend_client)
    proxied_tools: dict[str, FastMCPTool] = await proxy_server.get_tools()

    frontend_server = FastMCP("FrontendServer")

    # 4. Get the tool from the proxied backend server
    if not isinstance(proxied_tools["first_echo_tool"], ProxyTool):
        raise ValueError("The tool to wrap is not a ProxyTool")

    # 5. Wrap the tool in an InterceptingProxyTool
    tool_to_wrap: ProxyTool = proxied_tools["first_echo_tool"]
    intercepted_tool = InterceptingProxyTool.from_proxy_tool(
        backend_client, tool_to_wrap
    )

    # 6. Add the proxy tool to the frontend server
    intercepted_tool.add_to_server(frontend_server)

    # 7. Use a client to call the proxied tool on the frontend server
    async with Client(frontend_server) as client:
        print("Calling first_echo_tool with input 'hello'")
        # Input arguments will be merged with field_defaults and field_values
        # and hook_parameters will be passed to hooks
        response = await client.call_tool(
            "first_echo_tool", {"text": "hello"}
        )
        print(f"Received response: {response}")

    # 8. Setup the second backend tool
    if not isinstance(proxied_tools["second_echo_tool"], ProxyTool):
        raise ValueError("The tool to wrap is not a ProxyTool")

    second_tool_to_wrap: ProxyTool = proxied_tools["second_echo_tool"]

    # 9. Setup the pre and post hooks, expose a new log_level argument on top of the existing tool
    def pre_hook(arguments: dict[str, Any], context: Context | None, log_level: str = "debug") -> None:
        print("Pre-hook called with arguments: ", arguments)
        print("Pre-hook called with context: ", context)
        print("Pre-hook called with log_level: ", log_level)

    def post_hook(
        response: list[TextContent | ImageContent | EmbeddedResource],
        context: Context | None,
    ) -> None:
        print("Post-hook called with response: ", response)
        print("Post-hook called with context: ", context)

    # 10. Setup the default arguments, text is normally required but we can set a default value
    default_args = {"text": "hello", "count": 20, "prefix": "Prefix: "}

    class HookParams(BaseModel):
        log_level: str = Field(description="The log level to use for the tool call.")

    # 11. Wrap the second tool in an InterceptingProxyTool
    second_intercepted_tool = InterceptingProxyTool.from_proxy_tool(
        backend_client,
        second_tool_to_wrap,
        extra_fields_schema=HookParams.model_json_schema(),
        pre_tool_call_hook=pre_hook,
        post_tool_call_hook=post_hook,
        field_defaults=default_args,
    )

    second_intercepted_tool.add_to_server(frontend_server)

    async with Client(frontend_server) as client:
        print("Calling second_echo_tool with input 'hello'")
        response = await client.call_tool(
            "second_echo_tool",
            arguments={"log_level": "debug"}
        )
        print(f"Received response: {response}")


if __name__ == "__main__":
    asyncio.run(main())
    # Note: In a real application, you would typically run the frontend_server
    # using frontend_server.run() to make it available for external clients.
    # For this example, we just demonstrate the tool call within the script.
