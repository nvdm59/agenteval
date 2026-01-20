"""Unit tests for adapters."""

import pytest
from agenteval.adapters import AdapterRegistry, list_adapters
from agenteval.adapters.base import BaseAdapter
from agenteval.schemas.execution import AgentMessage, AgentResponse, TokenUsage


@pytest.mark.unit
class TestAdapterRegistry:
    """Test adapter registry functionality."""

    def test_list_adapters(self):
        """Test listing registered adapters."""
        adapters = list_adapters()
        assert isinstance(adapters, list)
        assert "anthropic" in adapters

    def test_get_adapter_info(self):
        """Test getting adapter metadata."""
        info = AdapterRegistry.get_adapter_info("anthropic")
        assert info["name"] == "anthropic"
        assert info["supports_tools"] is True
        assert info["supports_streaming"] is True

    def test_get_unknown_adapter_raises(self, mock_adapter_config):
        """Test that getting unknown adapter raises ValueError."""
        with pytest.raises(ValueError, match="Unknown adapter"):
            AdapterRegistry.get_adapter("nonexistent", mock_adapter_config)

    def test_register_duplicate_adapter_raises(self):
        """Test that registering duplicate adapter raises ValueError."""

        with pytest.raises(ValueError, match="already registered"):

            @AdapterRegistry.register("anthropic")
            class DuplicateAdapter(BaseAdapter):
                async def execute(self, messages, tools=None, **kwargs):
                    pass

                async def stream_execute(self, messages, tools=None, **kwargs):
                    pass

                def get_token_usage(self):
                    return TokenUsage()

                def get_cost(self):
                    return 0.0

                @property
                def supports_tools(self):
                    return True

                @property
                def supports_streaming(self):
                    return True


@pytest.mark.unit
class TestTokenUsage:
    """Test TokenUsage schema."""

    def test_token_usage_addition(self):
        """Test adding two TokenUsage objects."""
        usage1 = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        usage2 = TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300)

        total = usage1 + usage2

        assert total.input_tokens == 300
        assert total.output_tokens == 150
        assert total.total_tokens == 450

    def test_token_usage_with_cache(self):
        """Test TokenUsage with cache tokens."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cache_read_tokens=20,
            cache_write_tokens=30,
        )

        assert usage.cache_read_tokens == 20
        assert usage.cache_write_tokens == 30


@pytest.mark.unit
class TestAgentMessage:
    """Test AgentMessage schema."""

    def test_create_user_message(self):
        """Test creating a user message."""
        from agenteval.schemas.execution import MessageRole

        msg = AgentMessage(role=MessageRole.USER, content="Hello")

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.name is None

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        from agenteval.schemas.execution import MessageRole

        msg = AgentMessage(role=MessageRole.ASSISTANT, content="Hi there!")

        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi there!"


@pytest.mark.unit
class TestAgentResponse:
    """Test AgentResponse schema."""

    def test_create_response(self, sample_messages, sample_token_usage):
        """Test creating an agent response."""
        response = AgentResponse(
            content="Response text",
            messages=sample_messages,
            tool_calls=[],
            token_usage=sample_token_usage,
            model="test-model",
        )

        assert response.content == "Response text"
        assert len(response.messages) == 2
        assert response.token_usage.total_tokens == 150
        assert response.model == "test-model"
