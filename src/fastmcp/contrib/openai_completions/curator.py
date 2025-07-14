from textwrap import dedent

from mcp.types import ContentBlock
from pydantic import Field

from fastmcp.server.context import Context
from fastmcp.utilities.completions import FastMCPToolCall
from fastmcp.utilities.components import FastMCPComponent

RO_CURATOR_DESCRIPTION = """
Ask the Server's Tool Curator for help with your task. They will determine which tools to use
and will recommend which tools to use.
"""

RO_CURATOR_SYSTEM_PROMPT = """
You are a Tool curator called `{name}` that is embedded into this FastMCP Server. You act as a helpful assistant
that can recommend which tools from this server the user would use to complete a task.

You are described as:
```markdown
{description}
```

The tools available on the Server include:
```markdown
{tools}
```

For each recommendation, you should describe why the tool is the apprioriate tool, any items to consider before calling the tool,
and if you have enough information, you should also recommend which parameters to use for each tool.

The next message is the task you are being asked to assist with.
"""


class ReadOnlyCuratorAgent(FastMCPComponent):
    description: str = Field(default=RO_CURATOR_DESCRIPTION)

    system_prompt: str = Field(default=RO_CURATOR_SYSTEM_PROMPT)

    async def __call__(self, ctx: Context, task: str) -> ContentBlock:
        tools = await ctx.fastmcp.get_tools()

        tools_strs: list[str] = [
            dedent(f"""
            Tool: {tool.name}
            Description: {tool.description}
            Arguments (JSON Schema):
            ```json
            {tool.parameters}
            ```
            """).strip()
            for tool in tools.values()
        ]

        return await ctx.completions.text(
            system_prompt=self.system_prompt.format(
                name=self.name,
                description=self.description,
                tools="\n\n".join(tools_strs),
            ),
            messages=task,
        )


CURATOR_DESCRIPTION = """
Ask the Server's Tool Curator for help with your task. They will determine which tools to use
and will call them on your behalf.
"""

CURATOR_SYSTEM_PROMPT = """
You are a Tool curator called `{name}` that is embedded into this FastMCP Server. You act as a helpful assistant
that can call tools from this server on behalf of the user.

You are described as:
```markdown
{description}
```

The next message is the task you are being asked to assist with.
"""


class ToolCallingCuratorAgent(FastMCPComponent):
    """
    A tool calling curator agent that we tell can call tools on behalf of the user but really it can't
    and we just return the tool calls it would have made back to the user.
    """

    description: str = Field(default=CURATOR_DESCRIPTION)

    system_prompt: str = Field(default=CURATOR_SYSTEM_PROMPT)

    async def __call__(self, ctx: Context, task: str) -> list[ContentBlock]:
        tools = await ctx.fastmcp.get_tools()

        recommended_tool_call: FastMCPToolCall = await ctx.completions.tools(
            system_prompt=self.system_prompt.format(
                name=self.name,
                description=self.description,
            ),
            messages=task,
            parallel_tool_calls=False,
            tools=tools,
        )

        return await ctx.completions.call_tool(recommended_tool_call)