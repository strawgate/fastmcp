from asyncio import run

from fastmcp import FastMCP
from fastmcp.contrib.transforming_mcp_config.transforming_mcp_config import (
    TransformingMCPConfig,
    TransformingStdioMCPServer,
)
from fastmcp.tools.tool_transform import ArgTransformRequest, ToolTransformRequest


async def main():
    print("Hello from fastmcp-experiments!")

    mcp_config = TransformingMCPConfig(
        mcpServers={
            "stdio": TransformingStdioMCPServer(
                command="uvx",
                args=["mcp-server-fetch"],
                tools={
                    "fetch": ToolTransformRequest(
                        name="run_spot_run",
                        arguments={
                            "url": ArgTransformRequest(
                                name="bark",
                                description="bark bark bark",
                                default="woof woof woof",
                            )
                        },
                    )
                },
            )
        }
    )

    proxy = FastMCP.as_proxy(mcp_config)

    await proxy.run_async(transport="sse")


if __name__ == "__main__":
    run(main())
