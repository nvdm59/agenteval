"""Anthropic Claude adapter."""

import anthropic
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
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00,
        "cache_write": 3.75,
        "cache_read": 0.30,
    },
    "claude-3-opus-20240229": {
        "input": 15.00,
        "output": 75.00,
    },
    "claude-3-sonnet-20240229": {
        "input": 3.00,
        "output": 15.00,
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
    },
}


@AdapterRegistry.register(
    "anthropic",
    description="Anthropic Claude adapter with tool support",
    supports_tools=True,
    supports_streaming=True,
)
class AnthropicAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic adapter.

        Args:
            config: Configuration dictionary with:
                - api_key: Anthropic API key
                - model: Model name (e.g., "claude-3-5-sonnet-20241022")
                - max_tokens: Maximum tokens to generate (default: 4096)
                - temperature: Temperature for sampling (default: 1.0)
        """
        super().__init__(config)

        self.api_key = config.get("api_key")
        self.model = config.get("model", "claude-3-5-sonnet-20241022")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 1.0)

        # Initialize client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def execute(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict]] = None,
        max_turns: int = 10,
        **kwargs,
    ) -> AgentResponse:
        """
        Execute agent with Claude.

        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            max_turns: Maximum turns (for agentic loops)
            **kwargs: Additional arguments for Claude API

        Returns:
            AgentResponse with result
        """
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Extract system message if present
        system_message = None
        if messages and messages[0].role == MessageRole.SYSTEM:
            system_message = messages[0].content
            anthropic_messages = anthropic_messages[1:]

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": anthropic_messages,
            **kwargs,
        }

        if system_message:
            api_params["system"] = system_message

        if tools:
            api_params["tools"] = self._convert_tools(tools)

        # Call API
        response = await self.client.messages.create(**api_params)

        # Convert response
        agent_response = self._convert_response(response, messages)

        # Update usage
        if response.usage:
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
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
        anthropic_messages = self._convert_messages(messages)

        system_message = None
        if messages and messages[0].role == MessageRole.SYSTEM:
            system_message = messages[0].content
            anthropic_messages = anthropic_messages[1:]

        # Prepare parameters
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": anthropic_messages,
            **kwargs,
        }

        if system_message:
            api_params["system"] = system_message

        if tools:
            api_params["tools"] = self._convert_tools(tools)

        # Stream response
        accumulated_content = ""

        async with self.client.messages.stream(**api_params) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            accumulated_content += event.delta.text

                            # Yield partial response
                            yield AgentResponse(
                                content=accumulated_content,
                                messages=messages,
                                tool_calls=[],
                                model=self.model,
                                metadata={"streaming": True},
                            )

            # Get final message
            final_message = await stream.get_final_message()

            # Update usage
            if final_message.usage:
                usage = TokenUsage(
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                    total_tokens=final_message.usage.input_tokens
                    + final_message.usage.output_tokens,
                )
                self._update_usage(usage)

                # Calculate cost
                cost = self._calculate_cost(final_message.usage)
                self._update_cost(cost)

    def get_token_usage(self) -> TokenUsage:
        """Get cumulative token usage."""
        return self._token_usage

    def get_cost(self) -> float:
        """Get cumulative cost in USD."""
        return self._total_cost

    @property
    def supports_tools(self) -> bool:
        """Claude supports tool calling."""
        return True

    @property
    def supports_streaming(self) -> bool:
        """Claude supports streaming."""
        return True

    def _convert_messages(self, messages: List[AgentMessage]) -> List[Dict]:
        """Convert AgentMessage to Anthropic format."""
        converted = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # Handle separately

            converted.append(
                {
                    "role": msg.role.value if msg.role != MessageRole.ASSISTANT else "assistant",
                    "content": msg.content,
                }
            )
        return converted

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert tool definitions to Anthropic format."""
        converted = []
        for tool in tools:
            converted.append(
                {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("parameters", {}),
                }
            )
        return converted

    def _convert_response(
        self, response: anthropic.types.Message, original_messages: List[AgentMessage]
    ) -> AgentResponse:
        """Convert Anthropic response to AgentResponse."""
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        tool=block.name,
                        arguments=block.input,
                    )
                )

        return AgentResponse(
            content=content,
            messages=original_messages,
            tool_calls=tool_calls,
            model=response.model,
            finish_reason=response.stop_reason,
            metadata={
                "message_id": response.id,
                "stop_sequence": response.stop_sequence,
            },
        )

    def _calculate_cost(self, usage: Any) -> float:
        """Calculate cost based on token usage."""
        if not usage or self.model not in ANTHROPIC_PRICING:
            return 0.0

        pricing = ANTHROPIC_PRICING[self.model]

        # Cost in USD (pricing is per million tokens)
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]

        # Add cache costs if available
        cache_cost = 0.0
        if hasattr(usage, "cache_creation_input_tokens") and usage.cache_creation_input_tokens:
            cache_cost += (usage.cache_creation_input_tokens / 1_000_000) * pricing.get(
                "cache_write", 0
            )
        if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
            cache_cost += (usage.cache_read_input_tokens / 1_000_000) * pricing.get(
                "cache_read", 0
            )

        return input_cost + output_cost + cache_cost
