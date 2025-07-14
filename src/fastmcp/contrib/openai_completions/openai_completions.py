import json
from copy import deepcopy
from typing import Any, Literal

from mcp.types import (
    CallToolRequestParams,
    ContentBlock,
    TextContent,
)
from openai import OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared.chat_model import ChatModel
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import TypeAdapter
from typing_extensions import override

from fastmcp.tools import Tool
from fastmcp.utilities.completions import (
    CompletionMessage,
    CompletionMessages,
    FastMCPToolCall,
    LLMCompletionsProtocol,
)


class OpenAILLMCompletions(LLMCompletionsProtocol):
    def __init__(self, default_model: ChatModel, client: OpenAI | None = None):
        self.client: OpenAI = client or OpenAI()
        self.default_model: ChatModel = default_model

    @override
    async def text(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        response_type: Literal["mcp", "llm"] = "mcp",
        **kwargs: Any,
    ) -> CompletionMessage | ContentBlock:
        openai_messages = convert_messages_to_openai_messages(system_prompt, messages)

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
                if response_type == "mcp":
                    return get_content_block_from_completion_message(message)
                return message

        raise ValueError("No content in response from completion")

    @override
    async def tools(
        self,
        system_prompt: str,
        messages: str | CompletionMessages,
        tools: list[Tool] | dict[str, Tool],
        parallel_tool_calls: bool = True,
        response_type: Literal["fastmcp", "raw"] = "fastmcp",
        **kwargs: Any,
    ) -> CompletionMessage | list[FastMCPToolCall] | FastMCPToolCall:
        openai_messages = convert_messages_to_openai_messages(system_prompt, messages)

        if isinstance(tools, dict):
            tools = list(tools.values())

        openai_tools = [
            convert_fastmcp_tool_to_openai_tool_param_message(tool) for tool in tools
        ]

        completion_message: ChatCompletion = self.client.chat.completions.create(
            model=self.default_model,
            messages=openai_messages,
            parallel_tool_calls=parallel_tool_calls,
            tools=openai_tools,
            tool_choice="required",
            **kwargs,
        )

        if not (first_choice := completion_message.choices[0]):
            raise ValueError("No choices to pick from in the chat completion response.")

        if not isinstance(first_choice.message, ChatCompletionMessage):
            raise TypeError(
                "Unexpected message type in the first choice of the chat completion response."
            )

        if response_type == "fastmcp":
            fastmcp_tool_calls = convert_chat_completion_message_to_fastmcp_tool_calls(
                tools, first_choice.message
            )
            if parallel_tool_calls:
                return fastmcp_tool_calls

            return fastmcp_tool_calls[0]

        return first_choice.message


def convert_messages_to_openai_messages(
    system_prompt: str,
    messages: str | CompletionMessages,
) -> list[ChatCompletionMessageParam]:
    """Convert messages to OpenAI messages."""

    openai_messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=system_prompt)
    ]

    if isinstance(messages, str):
        openai_messages.append(
            ChatCompletionUserMessageParam(role="user", content=messages)
        )

        return openai_messages

    type_adapter = TypeAdapter(ChatCompletionMessageParam)

    for message in messages:
        openai_messages.append(type_adapter.validate_python(message))

    return openai_messages


def convert_chat_completion_message_to_fastmcp_tool_calls(
    tools: list[Tool],
    chat_completion_message: ChatCompletionMessage,
) -> list[tuple[Tool, dict[str, Any]]]:
    if not (tool_calls := chat_completion_message.tool_calls):
        raise ValueError("No tool_call in the chat completion message.")

    tools_by_name = {tool.name: tool for tool in tools}

    fastmcp_tool_calls: list[tuple[Tool, dict[str, Any]]] = []

    for tool_call in tool_calls:
        if not (function_call := tool_call.function):
            raise ValueError("No function call in the tool call.")

        if not (tool_name := tool_call.function.name):
            raise ValueError("No name in the function call of the tool call.")

        if tool_name not in tools_by_name:
            raise ValueError(f"Tool {tool_name} not found in the list of tools.")

        tool = tools_by_name[tool_name]

        fastmcp_tool_calls.append((tool, json.loads(function_call.arguments)))

    return fastmcp_tool_calls


def convert_fastmcp_tool_to_openai_tool_param_message(
    fastmcp_tool: Tool,
) -> ChatCompletionToolParam:
    """Convert an FastMCP tool to an OpenAI tool."""

    tool_name = fastmcp_tool.name
    tool_description = fastmcp_tool.description or ""
    tool_parameters = deepcopy(fastmcp_tool.parameters)

    return ChatCompletionToolParam(
        type="function",
        function=FunctionDefinition(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters,
            strict=False,
        ),
    )


def get_call_tool_request_params_from_completion_message(
    chat_completion_message: ChatCompletionMessage,
) -> list[CallToolRequestParams]:
    if not (tool_calls := chat_completion_message.tool_calls):
        raise ValueError("No tool_call in the chat completion message.")

    if len(tool_calls) == 0:
        raise ValueError("Zero tool calls in the chat completion message.")

    call_tool_request_params: list[CallToolRequestParams] = []

    for tool_call in tool_calls:
        if not (function_call := tool_call.function):
            raise ValueError("No function call in the tool call.")

        call_tool_request_params.append(
            CallToolRequestParams(
                name=function_call.name,
                arguments=json.loads(function_call.arguments),
            )
        )

    return call_tool_request_params


def get_content_block_from_completion_message(
    completion_message: CompletionMessage,
) -> ContentBlock:
    if isinstance(completion_message, dict):
        return TextContent(type="text", text=completion_message["content"])

    if isinstance(completion_message, ChatCompletionMessage):
        if content := completion_message.content:
            return TextContent(type="text", text=content)
        if refusal := completion_message.refusal:
            return TextContent(type="text", text=refusal)
        raise ValueError("Only Text content is supported.")

    raise ValueError("Only Text content is supported.")
