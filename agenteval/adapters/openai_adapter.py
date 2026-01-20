"""OpenAI GPT adapter."""

from openai import AsyncOpenAI
from typing import Any, AsyncIterator, Dict, List, Optional

from agenteval.adapters.base import BaseAdapter
from agenteval.adapters.registry import AdapterRegistry
from agenteval.schemas.execution import (
    AgentMessage,
    AgentResponse,
    MessageRole,
    TokenUsage,
    ToolCall,
)


# Pricing per million tokens (as of Jan 2026)
OPENAI_PRICING = {
    "gpt-4": {
        "input": 30.00,
        "output": 60.00,
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    },
}


@AdapterRegistry.register(
    "openai",
    description="OpenAI GPT adapter with function calling support",
    supports_tools=True,
    supports_streaming=True,
)
class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI GPT models."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI adapter.

        Args:
            config: Configuration dictionary with:
                - api_key: OpenAI API key
                - model: Model name (e.g., "gpt-4o", "gpt-4-turbo")
                - max_tokens: Maximum tokens to generate (default: 4096)
                - temperature: Temperature for sampling (default: 1.0)
        """
        super().__init__(config)

        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 1.0)

        # Initialize client
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def execute(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict]] = None,
        max_turns: int = 10,
        **kwargs,
    ) -> AgentResponse:
        """
        Execute agent with GPT.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            max_turns: Maximum turns (for agentic loops)
            **kwargs: Additional arguments for OpenAI API

        Returns:
            AgentResponse with result
        """
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            **kwargs,
        }

        if tools:
            api_params["tools"] = self._convert_tools(tools)

        # Call API
        response = await self.client.chat.completions.create(**api_params)

        # Convert response
        agent_response = self._convert_response(response, messages)

        # Update usage
        if response.usage:
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            self._update_usage(usage)
            agent_response.token_usage = usage

        # Calculate cost
        cost = self._calculate_cost(response.usage)
        self._update_cost(cost)

        return agent_response

    async def stream_execute(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> AsyncIterator[AgentResponse]:
        """
        Stream agent execution.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            **kwargs: Additional arguments

        Yields:
            AgentResponse objects as they arrive
        """
        # Convert messages
        openai_messages = self._convert_messages(messages)

        # Prepare parameters
        api_params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
            **kwargs,
        }

        if tools:
            api_params["tools"] = self._convert_tools(tools)

        # Stream response
        accumulated_content = ""
        accumulated_tool_calls = []

        stream = await self.client.chat.completions.create(**api_params)

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Accumulate content
            if delta.content:
                accumulated_content += delta.content

                # Yield partial response
                yield AgentResponse(
                    content=accumulated_content,
                    messages=messages,
                    tool_calls=accumulated_tool_calls,
                    model=self.model,
                    metadata={"streaming": True},
                )

            # Handle tool calls (for GPT-4 with function calling)
            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    if tool_call.function:
                        accumulated_tool_calls.append(
                            ToolCall(
                                id=tool_call.id or "unknown",
                                tool=tool_call.function.name or "unknown",
                                arguments=tool_call.function.arguments or {},
                            )
                        )

            # Check for finish
            if chunk.choices[0].finish_reason:
                # Note: Usage info not available in streaming mode
                # We'd need to estimate or track separately
                break

    def get_token_usage(self) -> TokenUsage:
        """Get cumulative token usage."""
        return self._token_usage

    def get_cost(self) -> float:
        """Get cumulative cost in USD."""
        return self._total_cost

    @property
    def supports_tools(self) -> bool:
        """GPT-4 and later support function calling."""
        return "gpt-4" in self.model or "gpt-3.5" in self.model

    @property
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True

    def _convert_messages(self, messages: List[AgentMessage]) -> List[Dict]:
        """Convert AgentMessage to OpenAI format."""
        converted = []
        for msg in messages:
            role_map = {
                MessageRole.USER: "user",
                MessageRole.ASSISTANT: "assistant",
                MessageRole.SYSTEM: "system",
                MessageRole.TOOL: "tool",
            }

            message_dict = {
                "role": role_map.get(msg.role, "user"),
                "content": msg.content,
            }

            if msg.name:
                message_dict["name"] = msg.name

            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id

            converted.append(message_dict)

        return converted

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert tool definitions to OpenAI format."""
        converted = []
        for tool in tools:
            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    },
                }
            )
        return converted

    def _convert_response(self, response: Any, original_messages: List[AgentMessage]) -> AgentResponse:
        """Convert OpenAI response to AgentResponse."""
        if not response.choices:
            return AgentResponse(
                content="",
                messages=original_messages,
                tool_calls=[],
                model=self.model,
                finish_reason="error",
            )

        choice = response.choices[0]
        message = choice.message

        content = message.content or ""
        tool_calls = []

        # Extract tool calls if present
        if message.tool_calls:
            for tc in message.tool_calls:
                # Parse arguments (they come as JSON string)
                import json

                try:
                    arguments = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        tool=tc.function.name,
                        arguments=arguments,
                    )
                )

        return AgentResponse(
            content=content,
            messages=original_messages,
            tool_calls=tool_calls,
            model=response.model,
            finish_reason=choice.finish_reason,
            metadata={
                "response_id": response.id,
                "created": response.created,
            },
        )

    def _calculate_cost(self, usage: Any) -> float:
        """Calculate cost based on token usage."""
        if not usage:
            return 0.0

        # Find pricing for model (try exact match first, then prefix)
        pricing = None
        for model_key in OPENAI_PRICING:
            if self.model.startswith(model_key):
                pricing = OPENAI_PRICING[model_key]
                break

        if not pricing:
            # Default to gpt-4o pricing if unknown
            pricing = OPENAI_PRICING["gpt-4o"]

        # Cost in USD (pricing is per million tokens)
        input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
