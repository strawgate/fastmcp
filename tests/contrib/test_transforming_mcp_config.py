# from asyncio import run
# from typing import Any
# import pytest
# from fastmcp import FastMCP
# from fastmcp.tools.tool import Tool as FastMCPTool
# from fastmcp.contrib.transforming_mcp_config.transforming_mcp_config import ToolTransformRequest, ArgTransformRequest


# def sample_tool_fn(arg1: int, arg2: str) -> str:
#     return f"Hello, world! {arg1} {arg2}"

# @pytest.fixture
# def sample_tool() -> FastMCPTool:
#     return FastMCPTool.from_function(sample_tool_fn, name="sample_tool")

# async def test_tool_transform_request(sample_tool: FastMCPTool):
#     transformed_tool = ToolTransformRequest(
#         arguments={
#             "arg1": ArgTransformRequest(
#                 name="transformed_arg1",
#                 description="The transformed first argument",
#                 default=10,
#             )
#         }
#     ).apply(sample_tool)

#     assert transformed_tool.name == "sample_tool"

#     properties: dict[str, Any] | None = transformed_tool.parameters.get("properties")

#     assert properties is not None

#     transformed_arg1: dict[str, Any] | None = properties.get("transformed_arg1")

#     assert transformed_arg1 is not None

#     assert transformed_arg1["title"] == "transformed_arg1"
#     assert transformed_arg1["description"] == "The transformed first argument"
#     assert transformed_arg1["default"] == 10


