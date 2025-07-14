from typing import Any

from mcp.types import TextContent
from openai import OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
)
from openai.types.shared.chat_model import ChatModel
from pydantic import TypeAdapter
from typing_extensions import override

from fastmcp.utilities.types import (
    CompletionMessage,
    CompletionMessages,
    ContentBlock,
    LLMCompletionsProtocol,
)


class OpenAILLMCompletions(LLMCompletionsProtocol):
    def __init__(self, default_model: ChatModel, client: OpenAI | None = None):
        self.client: OpenAI = client or OpenAI()
        self.default_model: ChatModel = default_model

    async def __call__(
        self,
        system_prompt: str,
        messages: CompletionMessages,
        **kwargs: Any,
    ) -> CompletionMessage:
        type_adapter = TypeAdapter(ChatCompletionMessageParam)

        openai_messages = []

        for message in messages:
            if isinstance(message, dict):
                openai_messages.append(type_adapter.validate_python(message))
            else:
                openai_messages.append(message)

        response: ChatCompletion = self.client.chat.completions.create(
            model=self.default_model,
            messages=openai_messages,
            **kwargs,
        )

        if len(response.choices) == 0:
            raise ValueError("No response for completion")

        first_choice = response.choices[0]

        if message := first_choice.message:
            if isinstance(message, ChatCompletionMessage):
                return message

        raise ValueError("No content in response from completion")

    @override
    @classmethod
    def get_content_block_from_completion(cls, completion: CompletionMessage) -> ContentBlock:
        if isinstance(completion, dict):
            return TextContent(type="text", text=completion["content"])

        if isinstance(completion, ChatCompletionMessage):
            if content := completion.content:
                return TextContent(type="text", text=content)
            if refusal := completion.refusal:
                return TextContent(type="text", text=refusal)
            raise ValueError("Only Text content is supported.")

        raise ValueError("Only Text content is supported.")