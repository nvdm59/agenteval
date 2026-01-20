"""Metrics system for evaluating agent performance."""

from agenteval.metrics.base import (
    BaseMetric,
    MetricRegistry,
    get_metric,
    list_metrics,
)

# Import metrics to trigger registration
from agenteval.metrics.success.completion_rate import CompletionRateMetric
from agenteval.metrics.efficiency.token_usage import (
    TokenUsageMetric,
    InputTokensMetric,
    OutputTokensMetric,
)
from agenteval.metrics.efficiency.execution_time import (
    ExecutionTimeMetric,
    APICostMetric,
    TurnsToCompletionMetric,
)
from agenteval.metrics.quality.accuracy import (
    AccuracyMetric,
    FuzzyMatchMetric,
    OutputLengthMetric,
)
from agenteval.metrics.safety.instruction_following import (
    InstructionFollowingMetric,
    HarmfulContentMetric,
    RefusalRateMetric,
)

__all__ = [
    # Base classes
    "BaseMetric",
    "MetricRegistry",
    "get_metric",
    "list_metrics",
    # Success metrics
    "CompletionRateMetric",
    # Efficiency metrics
    "TokenUsageMetric",
    "InputTokensMetric",
    "OutputTokensMetric",
    "ExecutionTimeMetric",
    "APICostMetric",
    "TurnsToCompletionMetric",
    # Quality metrics
    "AccuracyMetric",
    "FuzzyMatchMetric",
    "OutputLengthMetric",
    # Safety metrics
    "InstructionFollowingMetric",
    "HarmfulContentMetric",
    "RefusalRateMetric",
]
