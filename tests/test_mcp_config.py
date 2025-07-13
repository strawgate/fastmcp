from fastmcp.client.transports import MCPConfigTransport
import inspect
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import yaml

from fastmcp import FastMCP
from fastmcp.client.auth.bearer import BearerAuth
from fastmcp.client.auth.oauth import OAuthClientProvider
from fastmcp.client.client import Client
from fastmcp.client.logging import LogMessage
from fastmcp.client.transports import (
    SSETransport,
    StdioTransport,
    StreamableHttpTransport,
)
from fastmcp.exceptions import ToolError
from fastmcp.mcp_config import (
    MCPConfig,
    RemoteMCPServer,
    StdioMCPServer,
    TransformingStdioMCPServer,
)
from fastmcp.tools.tool import Tool as FastMCPTool
from fastmcp.tools.tool_transform import ArgTransformConfig, ToolTransformConfig


def test_parse_single_stdio_config():
    config = {
        "mcpServers": {
            "test_server": {
                "command": "echo",
                "args": ["hello"],
            }
        }
    }
    mcp_config = MCPConfig.from_dict(config)
    transport = mcp_config.mcpServers["test_server"].to_transport()
    assert isinstance(transport, StdioTransport)
    assert transport.command == "echo"
    assert transport.args == ["hello"]


def test_parse_extra_keys():
    config = {
        "mcpServers": {
            "test_server": {
                "command": "echo",
                "args": ["hello"],
                "leaf_extra": "leaf_extra",
            }
        },
        "root_extra": "root_extra",
    }
    mcp_config = MCPConfig.from_dict(config)
    
    serialized_mcp_config = mcp_config.model_dump()
    assert serialized_mcp_config["root_extra"] == "root_extra"
    assert serialized_mcp_config["mcpServers"]["test_server"]["leaf_extra"] == "leaf_extra"


def test_parse_single_remote_config():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000",
            }
        }
    }
    mcp_config = MCPConfig.from_dict(config)
    transport = mcp_config.mcpServers["test_server"].to_transport()
    assert isinstance(transport, StreamableHttpTransport)
    assert transport.url == "http://localhost:8000"


def test_parse_remote_config_with_transport():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000",
                "transport": "sse",
            }
        }
    }
    mcp_config = MCPConfig.from_dict(config)
    transport = mcp_config.mcpServers["test_server"].to_transport()
    assert isinstance(transport, SSETransport)
    assert transport.url == "http://localhost:8000"


def test_parse_remote_config_with_url_inference():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000/sse/",
            }
        }
    }
    mcp_config = MCPConfig.from_dict(config)
    transport = mcp_config.mcpServers["test_server"].to_transport()
    assert isinstance(transport, SSETransport)
    assert transport.url == "http://localhost:8000/sse/"


def test_parse_multiple_servers():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000/sse/",
            },
            "test_server_2": {
                "command": "echo",
                "args": ["hello"],
                "env": {"TEST": "test"},
            },
        }
    }
    mcp_config = MCPConfig.from_dict(config)
    assert len(mcp_config.mcpServers) == 2
    assert isinstance(mcp_config.mcpServers["test_server"], RemoteMCPServer)
    assert isinstance(mcp_config.mcpServers["test_server"].to_transport(), SSETransport)

    assert isinstance(mcp_config.mcpServers["test_server_2"], StdioMCPServer)
    assert isinstance(
        mcp_config.mcpServers["test_server_2"].to_transport(), StdioTransport
    )
    assert mcp_config.mcpServers["test_server_2"].command == "echo"
    assert mcp_config.mcpServers["test_server_2"].args == ["hello"]
    assert mcp_config.mcpServers["test_server_2"].env == {"TEST": "test"}


async def test_multi_client(tmp_path: Path):
    server_script = inspect.cleandoc("""
        from fastmcp import FastMCP

        mcp = FastMCP()

        @mcp.tool
        def add(a: int, b: int) -> int:
            return a + b

        if __name__ == '__main__':
            mcp.run()
        """)

    script_path = tmp_path / "test.py"
    script_path.write_text(server_script)

    config = {
        "mcpServers": {
            "test_1": {
                "command": "python",
                "args": [str(script_path)],
            },
            "test_2": {
                "command": "python",
                "args": [str(script_path)],
            },
        }
    }

    client = Client(config)

    async with client:
        tools = await client.list_tools()
        assert len(tools) == 2

        result_1 = await client.call_tool("test_1_add", {"a": 1, "b": 2})
        result_2 = await client.call_tool("test_2_add", {"a": 1, "b": 2})
        assert result_1.data == 3
        assert result_2.data == 3


async def test_remote_config_default_no_auth():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000",
            }
        }
    }
    client = Client(config)
    assert isinstance(client.transport.transport, StreamableHttpTransport)
    assert client.transport.transport.auth is None


async def test_remote_config_with_auth_token():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000",
                "auth": "test_token",
            }
        }
    }
    client = Client(config)
    assert isinstance(client.transport.transport, StreamableHttpTransport)
    assert isinstance(client.transport.transport.auth, BearerAuth)
    assert client.transport.transport.auth.token.get_secret_value() == "test_token"


async def test_remote_config_sse_with_auth_token():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000/sse/",
                "auth": "test_token",
            }
        }
    }
    client = Client(config)
    assert isinstance(client.transport.transport, SSETransport)
    assert isinstance(client.transport.transport.auth, BearerAuth)
    assert client.transport.transport.auth.token.get_secret_value() == "test_token"


async def test_remote_config_with_oauth_literal():
    config = {
        "mcpServers": {
            "test_server": {
                "url": "http://localhost:8000",
                "auth": "oauth",
            }
        }
    }
    client = Client(config)
    assert isinstance(client.transport.transport, StreamableHttpTransport)
    assert isinstance(client.transport.transport.auth, OAuthClientProvider)


async def test_multi_client_with_logging(tmp_path: Path):
    """
    Tests that logging is properly forwarded to the ultimate client.
    """
    server_script = inspect.cleandoc("""
        from fastmcp import FastMCP, Context

        mcp = FastMCP()

        @mcp.tool
        async def log_test(message: str, ctx: Context) -> int:
            await ctx.log(message)
            return 42

        if __name__ == '__main__':
            mcp.run()
        """)

    script_path = tmp_path / "test.py"
    script_path.write_text(server_script)

    config = {
        "mcpServers": {
            "test_server": {
                "command": "python",
                "args": [str(script_path)],
            },
            "test_server_2": {
                "command": "python",
                "args": [str(script_path)],
            },
        }
    }

    MESSAGES = []

    async def log_handler(message: LogMessage):
        MESSAGES.append(message)

    async with Client(config, log_handler=log_handler) as client:
        result = await client.call_tool("test_server_log_test", {"message": "test 42"})
        assert result.data == 42
        assert len(MESSAGES) == 1
        assert MESSAGES[0].data == "test 42"


async def test_multi_client_with_transforms(tmp_path: Path):
    """
    Tests that transforms are properly applied to the tools.
    """
    server_script = inspect.cleandoc("""
        from fastmcp import FastMCP

        mcp = FastMCP()

        @mcp.tool
        def add(a: int, b: int) -> int:
            return a + b

        if __name__ == '__main__':
            mcp.run()
        """)

    script_path = tmp_path / "test.py"
    script_path.write_text(server_script)

    config = {
        "mcpServers": {
            "test_1": {
                "command": "python",
                "args": [str(script_path)],
                "tools": {
                    "add": {
                        "name": "transformed_add",
                        "arguments": {
                            "a": {"name": "transformed_a"},
                            "b": {"name": "transformed_b"},
                        },
                    }
                },
            },
            "test_2": {
                "command": "python",
                "args": [str(script_path)],
            },
        }
    }

    client = Client[MCPConfigTransport](config)

    async with client:
        tools = await client.list_tools()
        tools_by_name = {tool.name: tool for tool in tools}
        assert len(tools) == 2
        assert "test_1_transformed_add" in tools_by_name


async def test_multi_client_with_elicitation(tmp_path: Path):
    """
    Tests that elicitation is properly forwarded to the ultimate client.
    """
    server_script = inspect.cleandoc("""
        from fastmcp import FastMCP, Context

        mcp = FastMCP()

        @mcp.tool
        async def elicit_test(ctx: Context) -> int:
            result = await ctx.elicit('Pick a number', response_type=int)
            return result.data

        if __name__ == '__main__':
            mcp.run()
        """)

    script_path = tmp_path / "test.py"
    script_path.write_text(server_script)

    config = {
        "mcpServers": {
            "test_server": {
                "command": "python",
                "args": [str(script_path)],
            },
            "test_server_2": {
                "command": "python",
                "args": [str(script_path)],
            },
        }
    }

    async def elicitation_handler(message, response_type, params, ctx):
        return response_type(value=42)

    async with Client(config, elicitation_handler=elicitation_handler) as client:
        result = await client.call_tool("test_server_elicit_test", {})
        assert result.data == 42


def sample_tool_fn(arg1: int, arg2: str) -> str:
    return f"Hello, world! {arg1} {arg2}"


@pytest.fixture
def sample_tool() -> FastMCPTool:
    return FastMCPTool.from_function(sample_tool_fn, name="sample_tool")


@pytest.fixture
async def test_script(tmp_path: Path) -> AsyncGenerator[Path, Any]:
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"""
        from fastmcp import FastMCP

        mcp = FastMCP()

        @mcp.tool
        def fetch(url: str) -> str:

            return f"Hello, world! {url}"

        if __name__ == '__main__':
            mcp.run()
        """)

        yield Path(f.name)

    pass


# async def test_transform_stdio_server(sample_tool: FastMCPTool, test_script: Path):
#     mcp_config = TransformingMCPConfig(
#         mcpServers={
#             "stdio": TransformingStdioMCPServer(
#                 command="python",
#                 args=[str(test_script)],
#                 tools={
#                     "fetch": ToolTransformConfig(
#                         name="run_spot_run",
#                         arguments={
#                             "url": ArgTransformConfig(
#                                 name="bark",
#                                 description="bark bark bark",
#                                 default="woof woof woof",
#                             )
#                         },
#                     )
#                 },
#             )
#         }
#     )

#     proxy = FastMCP.as_proxy(mcp_config)

#     tools = await proxy.get_tools()

#     assert "run_spot_run" in tools

#     run_spot_run = tools["run_spot_run"]

#     assert run_spot_run.name == "run_spot_run"

#     with pytest.raises(ToolError, match="Input should be a valid URL"):
#         _ = await run_spot_run.run(arguments={"bark": "woof woof woof"})


# async def test_transform_stdio_server_from_yaml(sample_tool: FastMCPTool, test_script: Path):
#     yaml_config = f"""
#     mcpServers:
#         fetch:
#             command: python
#             args:
#                 - {str(test_script)}
#             env:
#                 PYTHONIOENCODING: utf-8
#             tools:
#                 fetch:
#                     name: run_spot_run
#                     arguments:
#                         url:
#                             name: bark
#                             description: bark bark bark
#                             default: woof woof woof
#     """

#     mcp_config = TransformingMCPConfig.from_dict(yaml.safe_load(yaml_config))

#     proxy = FastMCP.as_proxy(mcp_config)

#     tools = await proxy.get_tools()

#     assert "run_spot_run" in tools

#     run_spot_run = tools["run_spot_run"]

#     assert run_spot_run.name == "run_spot_run"

#     with pytest.raises(ToolError, match="Input should be a valid URL"):
#         _ = await run_spot_run.run(arguments={"bark": "woof woof woof"})


# async def test_transform_stdio_server_from_dict(sample_tool: FastMCPTool, test_script: Path):
#     mcp_config = {
#         "mcpServers": {
#             "fetch": {
#                 "command": "python",
#                 "args": [str(test_script)],
#                 "env": {"PYTHONIOENCODING": "utf-8"},
#                 "tools": {
#                     "fetch": {
#                         "name": "run_spot_run",
#                         "arguments": {
#                             "url": {
#                                 "name": "bark",
#                                 "description": "bark bark bark",
#                                 "default": "woof woof woof",
#                             }
#                         },
#                     }
#                 },
#             }
#         }
#     }

#     mcp_config = TransformingMCPConfig.from_dict(mcp_config)

#     proxy = FastMCP.as_proxy(mcp_config)

#     tools = await proxy.get_tools()

#     assert "run_spot_run" in tools

#     run_spot_run = tools["run_spot_run"]

#     assert run_spot_run.name == "run_spot_run"

#     with pytest.raises(ToolError, match="Input should be a valid URL"):
#         _ = await run_spot_run.run(arguments={"bark": "woof woof woof"})
