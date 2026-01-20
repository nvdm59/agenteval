"""
AgentEval - Evaluation framework for LLM-based agents.

A comprehensive evaluation framework supporting multiple LLM providers,
benchmark suites, and detailed metrics for success, efficiency, quality,
and safety evaluation.
"""

from agenteval.version import __version__, __author__, __description__

# Core schemas
from agenteval.schemas import (
    # Benchmark schemas
    Benchmark,
    BenchmarkSuite,
    Task,
    TaskDefinition,
    # Execution schemas
    ExecutionResult,
    BenchmarkResult,
    AgentMessage,
    # Metrics schemas
    MetricResult,
    MetricsSummary,
)

# Adapters
from agenteval.adapters import (
    BaseAdapter,
    AdapterRegistry,
    get_adapter,
    list_adapters,
    AnthropicAdapter,
)

# Configuration
from agenteval.config import (
    AgentEvalSettings,
    get_settings,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__description__",
    # Schemas
    "Benchmark",
    "BenchmarkSuite",
    "Task",
    "TaskDefinition",
    "ExecutionResult",
    "BenchmarkResult",
    "AgentMessage",
    "MetricResult",
    "MetricsSummary",
    # Adapters
    "BaseAdapter",
    "AdapterRegistry",
    "get_adapter",
    "list_adapters",
    "AnthropicAdapter",
    # Configuration
    "AgentEvalSettings",
    "get_settings",
]
