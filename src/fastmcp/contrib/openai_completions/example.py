import asyncio
import os

from mcp.types import ContentBlock
from openai import OpenAI

from fastmcp import FastMCP
from fastmcp.contrib.openai_completions import OpenAILLMCompletions
from fastmcp.server.context import Context


async def async_main():
    server = FastMCP(
        name="OpenAI Completions Example",
        llm_completions=OpenAILLMCompletions(
            default_model=os.getenv("MODEL") or "gpt-4o-mini",  # pyright: ignore[reportArgumentType]
            client=OpenAI(
                api_key=os.getenv("API_KEY"),
                base_url=os.getenv("BASE_URL"),
            ),
        ),
    )

    @server.tool
    async def test_completion(ctx: Context) -> ContentBlock:
        result = await ctx.completion(
            system_prompt="You are a helpful assistant.",
            messages=[
                {"role": "user", "content": "What is the capital of France?"},
            ],
            response_type="mcp",
        )

        return result

    await server.run_sse_async()


if __name__ == "__main__":
    asyncio.run(async_main())
