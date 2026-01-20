"""Pytest configuration and fixtures for AgentEval tests."""

import pytest
from typing import Dict
from agenteval.config import AgentEvalSettings, set_settings


@pytest.fixture
def test_settings():
    """Provide test settings."""
    settings = AgentEvalSettings(
        log_level="DEBUG",
        cache_dir=".test_cache",
        trace_dir=".test_traces",
        save_traces=False,
        anthropic_api_key="test-key",
        openai_api_key="test-key",
    )
    set_settings(settings)
    return settings


@pytest.fixture
def sample_task_config() -> Dict:
    """Provide a sample task configuration."""
    return {
        "metadata": {
            "name": "test_task",
            "description": "A test task",
            "tags": ["test"],
            "difficulty": "easy",
        },
        "task": {
            "type": "general",
            "instructions": "Test instructions",
            "validation": {"method": "rule_based"},
        },
    }


@pytest.fixture
def mock_adapter_config() -> Dict:
    """Provide mock adapter configuration."""
    return {
        "api_key": "test-key",
        "model": "test-model",
        "max_tokens": 1024,
    }


@pytest.fixture
def sample_messages():
    """Provide sample conversation messages."""
    from agenteval.schemas.execution import AgentMessage, MessageRole

    return [
        AgentMessage(role=MessageRole.USER, content="Hello"),
        AgentMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
    ]


@pytest.fixture
def sample_token_usage():
    """Provide sample token usage."""
    from agenteval.schemas.execution import TokenUsage

    return TokenUsage(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_api: Tests that require API keys")
