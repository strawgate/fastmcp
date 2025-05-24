from typing import Any
from unittest.mock import MagicMock

import pytest
from mcp.types import EmbeddedResource, ImageContent, TextContent
from pydantic import BaseModel, Field

from fastmcp import Context, FastMCP
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.contrib.intercept_proxy_tool.intercept_proxy_tool import (
    InterceptingProxyTool,
)
from fastmcp.exceptions import ToolError


# Define a simple backend tool for testing
class BackendTool:
    def __init__(self):
        self.call_count = 0
        self.received_args = None

    async def run(
        self,
        required_arg_one: str,
        required_arg_two: str,
        optional_arg_three: str,
        context: Context | None = None,
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        self.call_count += 1
        self.received_args = {
            "required_arg_one": required_arg_one,
            "required_arg_two": required_arg_two,
            "optional_arg_three": optional_arg_three,
        }
        # Simulate a successful response
        return [
            TextContent(
                text=f"Backend received: {required_arg_one} {required_arg_two} {optional_arg_three}",
                type="text",
            )
        ]


@pytest.fixture
async def backend_server():
    server = FastMCP("BackendServer")
    backend_tool_instance = BackendTool()

    tool_name = "backend_tool"
    server.add_tool(backend_tool_instance.run, name=tool_name)

    # Get the tool from the backend server
    tools = await server.get_tools()
    tool = tools[tool_name]

    return server, backend_tool_instance, tool


@pytest.fixture
def backend_client(backend_server):
    server, _, _ = backend_server
    return Client(transport=FastMCPTransport(server))


@pytest.fixture
def frontend_server():
    return FastMCP("FrontendProxyServer")

class PreHook(BaseModel):
    pre_hook_arg: int = Field(description="An extra argument for the hook")
    post_hook_arg: int = Field(description="An extra argument for the hook")

    @classmethod
    def pre_hook(cls, arguments: dict[str, Any], context: Context | None) -> None:
        return None

    @classmethod
    def post_hook(cls, response: list[TextContent | ImageContent | EmbeddedResource], context: Context | None) -> None:
        return None


class TestInterceptingProxyTool:
    async def test_init_updates_parameters(self):
        extra_schema = {
            "type": "object",
            "properties": {
                "extra_arg": {
                    "title": "Extra Arg",
                    "description": "An extra argument for the hook",
                    "type": "integer",
                }
            },
            "required": ["extra_arg"],  # Assuming required for schema generation
        }

        proxy_tool = InterceptingProxyTool(
            client=MagicMock(),  # Mock client as it's not used in __init__
            name="test_tool",
            description="test description",
            parameters={},
            extra_fields_schema=extra_schema,
        )
        # Check that extra_fields_schema are added to the tool's parameters schema
        assert "extra_arg" in proxy_tool.parameters.get("properties", {})
        assert proxy_tool.parameters["properties"]["extra_arg"]["type"] == "integer"

    async def test_run_calls_hooks_and_proxied_tool(
        self, backend_server, backend_client, frontend_server
    ):
        _, backend_tool_instance, tool = backend_server

        intercepted_tool = InterceptingProxyTool.from_proxy_tool(
            client=backend_client,
            proxy_tool=tool,
            extra_fields_schema=PreHook.model_json_schema(),
            field_defaults={
                "required_arg_one": "required_arg_one_default",
                "required_arg_two": "required_arg_two_default",
            },
            field_values={
                "optional_arg_three": None,
            },
            pre_tool_call_hook=PreHook.pre_hook,
            post_tool_call_hook=PreHook.post_hook,
        )
        
        intercepted_tool.add_to_server(frontend_server)

        async with Client(frontend_server) as client:
            response = await client.call_tool(
                tool.name,
                {
                    "required_arg_one": "value",
                    "optional_arg_three": 123,
                },
            )

        # Verify pre_tool_call_hook was called with correct arguments and context
        mock_pre_hook.assert_called_once()
        called_args, called_context = mock_pre_hook.call_args[0]
        assert called_args == {"extra_arg": 123}
        assert called_context is None

        # Verify field_defaults and field_values were applied to arguments passed to backend tool
        assert backend_tool_instance.call_count == 1
        assert backend_tool_instance.received_args == {
            "some_arg": "value",
            "default_arg": "default_value",
            "mandatory_arg": "mandatory_value",
        }

        # Verify post_tool_call_hook was called with correct response and context
        mock_post_hook.assert_called_once()
        called_response, called_context = mock_post_hook.call_args[0]
        assert isinstance(called_response, list)
        assert isinstance(called_response[0], TextContent)
        assert (
            called_response[0].text
            == "Backend received: value default_value mandatory_value"
        )
        assert called_context is None

        # Verify the response from the proxied tool was returned
        assert isinstance(response, list)
        assert isinstance(response[0], TextContent)
        assert (
            response[0].text == "Backend received: value default_value mandatory_value"
        )

    async def test_run_without_hooks(
        self, backend_server, backend_client, frontend_server
    ):
        _, backend_tool_instance, tool = backend_server

        intercepted_tool = InterceptingProxyTool.from_proxy_tool(
            client=backend_client,
            proxy_tool=tool,
        )
        intercepted_tool.add_to_server(frontend_server)

        async with Client(frontend_server) as client:
            input_args = {
                "some_arg": "value",
                "default_arg": "default_value",
                "mandatory_arg": "mandatory_value",
            }
            response = await client.call_tool(tool.name, input_args)

        assert backend_tool_instance.call_count == 1
        assert backend_tool_instance.received_args == {
            "some_arg": "value",
            "default_arg": "default_value",
            "mandatory_arg": "mandatory_value",
        }

        assert isinstance(response, list)
        assert isinstance(response[0], TextContent)
        assert (
            response[0].text == "Backend received: value default_value mandatory_value"
        )

    async def test_run_with_field_defaults_only(
        self, backend_server, backend_client, frontend_server
    ):
        _, backend_tool_instance, tool = backend_server

        intercepted_tool = InterceptingProxyTool.from_proxy_tool(
            client=backend_client,
            proxy_tool=tool,
            field_defaults={
                "default_arg": "default_value",
                "mandatory_arg": "mandatory_value",
            },
        )
        intercepted_tool.add_to_server(frontend_server)

        async with Client(frontend_server) as client:
            input_args = {"some_arg": "value"}
            response = await client.call_tool(tool.name, input_args)

        assert backend_tool_instance.call_count == 1
        assert backend_tool_instance.received_args == {
            "some_arg": "value",
            "default_arg": "default_value",
            "mandatory_arg": "mandatory_value",
        }

        assert isinstance(response, list)
        assert isinstance(response[0], TextContent)
        assert (
            response[0].text == "Backend received: value default_value mandatory_value"
        )

    async def test_run_with_field_values_only(
        self, backend_server, backend_client, frontend_server
    ):
        _, backend_tool_instance, tool = backend_server

        intercepted_tool = InterceptingProxyTool.from_proxy_tool(
            client=backend_client,
            proxy_tool=tool,
            field_values={"mandatory_arg": "mandatory_value"},
        )
        intercepted_tool.add_to_server(frontend_server)

        async with Client(frontend_server) as client:
            input_args = {"some_arg": "value", "default_arg": "default_value"}
            response = await client.call_tool(tool.name, input_args)

        assert backend_tool_instance.call_count == 1
        assert backend_tool_instance.received_args == {
            "some_arg": "value",
            "default_arg": "default_value",
            "mandatory_arg": "mandatory_value",
        }

        assert isinstance(response, list)
        assert isinstance(response[0], TextContent)
        assert (
            response[0].text == "Backend received: value default_value mandatory_value"
        )

    async def test_run_field_values_override_defaults_and_input(
        self, backend_server, backend_client, frontend_server
    ):
        _, backend_tool_instance, tool = backend_server

        intercepted_tool = InterceptingProxyTool.from_proxy_tool(
            client=backend_client,
            proxy_tool=tool,
            field_defaults={"default_arg": "default_arg_default"},
            field_values={"mandatory_arg": "mandatory_value"},
        )
        intercepted_tool.add_to_server(frontend_server)

        async with Client(frontend_server) as client:
            input_args = {
                "some_arg": "input_value",
                "default_arg": "input_default",
                "mandatory_arg": "input_mandatory",
            }
            response = await client.call_tool(tool.name, input_args)

        assert backend_tool_instance.call_count == 1
        assert backend_tool_instance.received_args == {
            "some_arg": "input_value",
            "default_arg": "input_default",
            "mandatory_arg": "input_mandatory",
        }

        assert isinstance(response, list)
        assert isinstance(response[0], TextContent)
        assert (
            response[0].text
            == "Backend received: input_value input_default input_mandatory"
        )

        async with Client(frontend_server) as client:
            input_args = {
                "some_arg": "input_value",
                "default_arg": "",
                "mandatory_arg": "input_value",
                "other_arg": "other",
            }
            with pytest.raises(ToolError):
                response = await client.call_tool(tool.name, input_args)
