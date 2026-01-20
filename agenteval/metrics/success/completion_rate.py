"""Completion rate metric."""

from agenteval.metrics.base import BaseMetric, MetricRegistry
from agenteval.schemas.execution import ExecutionResult, ExecutionStatus
from agenteval.schemas.metrics import MetricResult, MetricType


@MetricRegistry.register(
    "completion_rate",
    description="Percentage of tasks that completed successfully",
    metric_type=MetricType.SUCCESS,
)
class CompletionRateMetric(BaseMetric):
    """
    Metric that tracks task completion rate.

    Returns 1.0 if task completed successfully, 0.0 otherwise.
    When aggregated across multiple tasks, gives the overall success rate.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is a success metric."""
        return MetricType.SUCCESS

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute completion rate for a single task.

        Args:
            result: Execution result

        Returns:
            MetricResult with 1.0 for success, 0.0 for failure
        """
        completed = result.status == ExecutionStatus.COMPLETED and result.success

        return MetricResult(
            name="completion_rate",
            value=1.0 if completed else 0.0,
            metric_type=self.metric_type,
            unit="rate",
            task_id=result.task_id,
            metadata={
                "status": result.status.value,
                "success": result.success,
                "validation_passed": result.validation_passed,
                "error": result.error if not completed else None,
            },
        )

    def get_unit(self) -> str:
        """Unit is rate (0.0 to 1.0)."""
        return "rate"
