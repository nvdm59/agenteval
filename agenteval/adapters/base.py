"""Base adapter class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from agenteval.schemas.execution import AgentMessage, AgentResponse, TokenUsage, ToolCall


class BaseAdapter(ABC):
    """
    Base class for all agent adapters.

    Adapters provide a unified interface for interacting with different
    LLM providers (Anthropic, OpenAI, Google, etc.) and agent frameworks.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration.

        Args:
            config: Configuration dictionary containing:
                - api_key: API key for the provider
                - model: Model name to use
                - Additional provider-specific settings
        """
        self.config = config
        self.metadata: Dict[str, Any] = {}
        self._token_usage = TokenUsage()
        self._total_cost = 0.0

    @abstractmethod
    async def execute(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict]] = None,
        max_turns: int = 10,
        **kwargs,
    ) -> AgentResponse:
        """
        Execute agent with given messages and tools.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tool definitions
            max_turns: Maximum number of turns to execute
            **kwargs: Additional provider-specific arguments

        Returns:
            AgentResponse with the result

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If execution fails
        """
        pass

    @abstractmethod
    async def stream_execute(
        self,
        messages: List[AgentMessage],
        tools: Optional[List[Dict]] = None,
        **kwargs,
    ) -> AsyncIterator[AgentResponse]:
        """
        Stream agent execution responses.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tool definitions
            **kwargs: Additional provider-specific arguments

        Yields:
            AgentResponse objects as they become available

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If execution fails
        """
        pass

    @abstractmethod
    def get_token_usage(self) -> TokenUsage:
        """
        Get token usage statistics for this adapter.

        Returns:
            TokenUsage object with input/output token counts
        """
        pass

    @abstractmethod
    def get_cost(self) -> float:
        """
        Calculate estimated cost based on token usage.

        Returns:
            Estimated cost in USD

        Note:
            Costs are estimates based on public pricing and may not
            reflect actual billing, especially for enterprise contracts.
        """
        pass

    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        """
        Check if this adapter supports tool calling.

        Returns:
            True if tool calling is supported, False otherwise
        """
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if this adapter supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        pass

    @property
    def adapter_name(self) -> str:
        """
        Get the name of this adapter.

        Returns:
            Adapter name (e.g., "anthropic/claude-3-5-sonnet")
        """
        provider = self.__class__.__name__.replace("Adapter", "").lower()
        model = self.config.get("model", "unknown")
        return f"{provider}/{model}"

    def reset_usage(self) -> None:
        """Reset token usage and cost tracking."""
        self._token_usage = TokenUsage()
        self._total_cost = 0.0

    def _update_usage(self, usage: TokenUsage) -> None:
        """
        Update cumulative token usage.

        Args:
            usage: TokenUsage from latest API call
        """
        self._token_usage += usage

    def _update_cost(self, cost: float) -> None:
        """
        Update cumulative cost.

        Args:
            cost: Cost from latest API call
        """
        self._total_cost += cost

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Dictionary with adapter information
        """
        return {
            "adapter_name": self.adapter_name,
            "model": self.config.get("model"),
            "supports_tools": self.supports_tools,
            "supports_streaming": self.supports_streaming,
            "token_usage": self.get_token_usage().model_dump(),
            "total_cost": self.get_cost(),
            **self.metadata,
        }

    async def validate_config(self) -> None:
        """
        Validate adapter configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if "api_key" not in self.config or not self.config["api_key"]:
            raise ValueError(f"{self.__class__.__name__} requires an API key")

        if "model" not in self.config or not self.config["model"]:
            raise ValueError(f"{self.__class__.__name__} requires a model name")

    def __repr__(self) -> str:
        """String representation of adapter."""
        return f"{self.__class__.__name__}(model={self.config.get('model')})"
