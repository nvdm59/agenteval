"""Agent adapters for different LLM providers."""

from agenteval.adapters.base import BaseAdapter
from agenteval.adapters.registry import AdapterRegistry, get_adapter, list_adapters

# Import adapters to trigger registration
from agenteval.adapters.anthropic_adapter import AnthropicAdapter
from agenteval.adapters.openai_adapter import OpenAIAdapter

__all__ = [
    "BaseAdapter",
    "AdapterRegistry",
    "get_adapter",
    "list_adapters",
    "AnthropicAdapter",
    "OpenAIAdapter",
]
