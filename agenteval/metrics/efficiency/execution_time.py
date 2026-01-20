"""Execution time metric."""

from agenteval.metrics.base import BaseMetric, MetricRegistry
from agenteval.schemas.execution import ExecutionResult
from agenteval.schemas.metrics import MetricResult, MetricType


@MetricRegistry.register(
    "execution_time",
    description="Time taken to execute the task in seconds",
    metric_type=MetricType.EFFICIENCY,
)
class ExecutionTimeMetric(BaseMetric):
    """
    Metric that tracks task execution time.

    Reports the time taken from start to end of task execution.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is an efficiency metric."""
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute execution time for a task.

        Args:
            result: Execution result

        Returns:
            MetricResult with execution time in seconds
        """
        execution_time = result.execution_time

        return MetricResult(
            name="execution_time",
            value=execution_time,
            metric_type=self.metric_type,
            unit="seconds",
            task_id=result.task_id,
            metadata={
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "status": result.status.value,
            },
        )

    def get_unit(self) -> str:
        """Unit is seconds."""
        return "seconds"


@MetricRegistry.register(
    "api_cost",
    description="Estimated API cost in USD",
    metric_type=MetricType.EFFICIENCY,
)
class APICostMetric(BaseMetric):
    """
    Metric that tracks estimated API costs.

    Reports the estimated cost of API calls for the task.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is an efficiency metric."""
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute API cost for a task.

        Args:
            result: Execution result

        Returns:
            MetricResult with cost in USD
        """
        cost = result.cost or 0.0

        return MetricResult(
            name="api_cost",
            value=cost,
            metric_type=self.metric_type,
            unit="USD",
            task_id=result.task_id,
            metadata={
                "adapter": result.adapter_name,
                "token_usage": result.token_usage.model_dump() if result.token_usage else None,
            },
        )

    def get_unit(self) -> str:
        """Unit is USD."""
        return "USD"


@MetricRegistry.register(
    "turns_to_completion",
    description="Number of agent turns to complete the task",
    metric_type=MetricType.EFFICIENCY,
)
class TurnsToCompletionMetric(BaseMetric):
    """
    Metric that tracks number of turns needed.

    Reports how many back-and-forth turns the agent needed.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is an efficiency metric."""
        return MetricType.EFFICIENCY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute turns to completion.

        Args:
            result: Execution result

        Returns:
            MetricResult with number of turns
        """
        turns = result.turns_count

        return MetricResult(
            name="turns_to_completion",
            value=float(turns),
            metric_type=self.metric_type,
            unit="turns",
            task_id=result.task_id,
            metadata={
                "success": result.success,
                "status": result.status.value,
            },
        )

    def get_unit(self) -> str:
        """Unit is turns."""
        return "turns"
