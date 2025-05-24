# Intercepting Proxy Tool

This module provides the `InterceptingProxyTool` class, a subclass of `ProxyTool` that allows for intercepting tool calls to a backend server. It enables modification of tool call arguments and processing of responses using pre and post hooks.

This is a community-contributed module and is located in the `contrib` directory. Please refer to the main [FastMCP Contrib Modules README](../README.md) for general information about contrib modules and their guarantees.

## Purpose

The `InterceptingProxyTool` is useful for scenarios where you need to:
- Modify arguments before they are sent to a proxied tool (e.g., adding default values, injecting mandatory parameters, transforming data).
- Execute custom logic before a tool call (e.g., logging, validation, rate limiting).
- Process the response from a proxied tool before returning it (e.g., filtering, transforming, logging).

## Installation

Since this is a contrib module, it is included with the FastMCP library. No separate installation is required.

## Usage

To use the `InterceptingProxyTool`, you need to:
1. Instantiate the `InterceptingProxyTool`, providing a client connected to the backend server and the name of the tool to proxy.
2. Optionally configure `extra_fields_schema`, `field_defaults`, `field_values`, `pre_tool_call_hook`, and `post_tool_call_hook`.
3. Add the `run` method of the `InterceptingProxyTool` instance to your frontend FastMCP server using `server.add_tool()`.

Alternatively, you can use the `InterceptingProxyTool.from_proxy_tool()` class method to create an instance from an existing `ProxyTool` definition retrieved from a backend server. This is the recommended approach when proxying tools from another FastMCP server.
See the [example.py](./example.py) file for a practical demonstration.

## Parameters

The `InterceptingProxyTool` accepts the following parameters during initialization:

- `client`: A `Client` instance connected to the backend FastMCP server. (Required)
- `name`: The name to register this proxy tool with on the frontend server. (Required)
- `description`: A description for the proxy tool. (Optional)
- `parameters`: The input schema for the proxy tool. If `extra_fields_schema` is provided, its fields will be added to this schema. (Optional)
- `extra_fields_schema`: A dictionary representing the JSON Schema of additional fields to include in the proxy tool's input schema. These fields will be passed to the pre and post hooks. (Optional)
- `field_defaults`: A dictionary of default values to apply to the arguments passed to the proxied tool. These defaults are applied before `field_values`. (Optional)
- `field_values`: A dictionary of mandatory values to apply to the arguments passed to the proxied tool. These values override any values provided in the input arguments or `field_defaults`. (Optional)
- `pre_tool_call_hook`: A callable function `(arguments: dict[str, Any], context: Context | None) -> None` that is executed before the proxied tool is called. The `arguments` dictionary will contain the fields defined in `hook_parameters`. (Optional)
- `post_tool_call_hook`: A callable function `(response: list[TextContent | ImageContent | EmbeddedResource], context: Context | None) -> None` that is executed after the proxied tool returns a response. (Optional)

## Example

Refer to [`./example.py`](./example.py) for a complete example demonstrating the usage of `InterceptingProxyTool` with hooks and argument modification.