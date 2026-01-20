"""Token usage metrics."""

from agenteval.metrics.base import BaseMetric, MetricRegistry
from agenteval.schemas.execution import ExecutionResult
from agenteval.schemas.metrics import MetricResult, MetricType


@MetricRegistry.register(
    "token_usage",
    description="Total number of tokens used (input + output)",
    metric_type=MetricType.EFFICIENCY,
)
class TokenUsageMetric(BaseMetric):
    """
    Metric that tracks token usage.

    Reports the total number of tokens (input + output) used for a task.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is an efficiency metric."""
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute token usage for a task.

        Args:
            result: Execution result

        Returns:
            MetricResult with total token count
        """
        if not result.token_usage:
            return MetricResult(
                name="token_usage",
                value=0.0,
                metric_type=self.metric_type,
                unit="tokens",
                task_id=result.task_id,
                metadata={"warning": "No token usage data available"},
            )

        total_tokens = result.token_usage.total_tokens

        return MetricResult(
            name="token_usage",
            value=float(total_tokens),
            metric_type=self.metric_type,
            unit="tokens",
            task_id=result.task_id,
            metadata={
                "input_tokens": result.token_usage.input_tokens,
                "output_tokens": result.token_usage.output_tokens,
                "cache_read_tokens": result.token_usage.cache_read_tokens,
                "cache_write_tokens": result.token_usage.cache_write_tokens,
            },
            details={
                "breakdown": {
                    "input": result.token_usage.input_tokens,
                    "output": result.token_usage.output_tokens,
                }
            },
        )

    def get_unit(self) -> str:
        """Unit is tokens."""
        return "tokens"


@MetricRegistry.register(
    "input_tokens",
    description="Number of input tokens used",
    metric_type=MetricType.EFFICIENCY,
)
class InputTokensMetric(BaseMetric):
    """Metric for input tokens only."""

    @property
    def metric_type(self) -> MetricType:
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """Compute input tokens."""
        value = result.token_usage.input_tokens if result.token_usage else 0

        return MetricResult(
            name="input_tokens",
            value=float(value),
            metric_type=self.metric_type,
            unit="tokens",
            task_id=result.task_id,
        )

    def get_unit(self) -> str:
        return "tokens"


@MetricRegistry.register(
    "output_tokens",
    description="Number of output tokens generated",
    metric_type=MetricType.EFFICIENCY,
)
class OutputTokensMetric(BaseMetric):
    """Metric for output tokens only."""

    @property
    def metric_type(self) -> MetricType:
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """Compute output tokens."""
        value = result.token_usage.output_tokens if result.token_usage else 0

        return MetricResult(
            name="output_tokens",
            value=float(value),
            metric_type=self.metric_type,
            unit="tokens",
            task_id=result.task_id,
        )

    def get_unit(self) -> str:
        return "tokens"
