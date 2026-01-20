"""Unit tests for metrics."""

import pytest
from datetime import datetime

from agenteval.metrics import (
    list_metrics,
    get_metric,
    CompletionRateMetric,
    TokenUsageMetric,
    ExecutionTimeMetric,
    AccuracyMetric,
    InstructionFollowingMetric,
)
from agenteval.schemas.execution import ExecutionResult, ExecutionStatus, TokenUsage


@pytest.mark.unit
class TestMetricRegistry:
    """Test metric registry functionality."""

    def test_list_metrics(self):
        """Test listing all metrics."""
        metrics = list_metrics()
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        assert "completion_rate" in metrics
        assert "token_usage" in metrics

    def test_get_metric(self):
        """Test getting a metric by name."""
        metric = get_metric("completion_rate")
        assert isinstance(metric, CompletionRateMetric)

    def test_get_unknown_metric_raises(self):
        """Test that getting unknown metric raises ValueError."""
        with pytest.raises(ValueError, match="Unknown metric"):
            get_metric("nonexistent_metric")


@pytest.mark.unit
class TestCompletionRateMetric:
    """Test completion rate metric."""

    def test_successful_task(self):
        """Test metric for successful task."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            adapter_name="test_adapter",
            validation_passed=True,
        )

        metric = CompletionRateMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 1.0
        assert metric_result.name == "completion_rate"

    def test_failed_task(self):
        """Test metric for failed task."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.FAILED,
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            error="Test error",
            adapter_name="test_adapter",
            validation_passed=False,
        )

        metric = CompletionRateMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 0.0


@pytest.mark.unit
class TestTokenUsageMetric:
    """Test token usage metric."""

    def test_with_token_usage(self):
        """Test metric with token usage data."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            adapter_name="test_adapter",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            validation_passed=True,
        )

        metric = TokenUsageMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 150.0
        assert metric_result.metadata["input_tokens"] == 100
        assert metric_result.metadata["output_tokens"] == 50

    def test_without_token_usage(self):
        """Test metric without token usage data."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            adapter_name="test_adapter",
            validation_passed=True,
        )

        metric = TokenUsageMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 0.0
        assert "warning" in metric_result.metadata


@pytest.mark.unit
class TestExecutionTimeMetric:
    """Test execution time metric."""

    def test_execution_time(self):
        """Test execution time measurement."""
        start = datetime.now()
        end = datetime.now()

        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=start,
            end_time=end,
            execution_time=2.5,
            adapter_name="test_adapter",
            validation_passed=True,
        )

        metric = ExecutionTimeMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 2.5
        assert metric_result.unit == "seconds"


@pytest.mark.unit
class TestAccuracyMetric:
    """Test accuracy metric."""

    def test_exact_match(self):
        """Test exact match accuracy."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            output="42",
            adapter_name="test_adapter",
            validation_passed=True,
            metadata={"expected_output": "42"},
        )

        metric = AccuracyMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 1.0
        assert metric_result.metadata["match"] is True

    def test_no_match(self):
        """Test no match accuracy."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            output="wrong answer",
            adapter_name="test_adapter",
            validation_passed=False,
            metadata={"expected_output": "42"},
        )

        metric = AccuracyMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 0.0
        assert metric_result.metadata["match"] is False


@pytest.mark.unit
class TestInstructionFollowingMetric:
    """Test instruction following metric."""

    def test_validation_passed(self):
        """Test with validation passed."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            adapter_name="test_adapter",
            validation_passed=True,
        )

        metric = InstructionFollowingMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 1.0

    def test_validation_failed(self):
        """Test with validation failed."""
        result = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.FAILED,
            success=False,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.0,
            adapter_name="test_adapter",
            validation_passed=False,
        )

        metric = InstructionFollowingMetric()
        metric_result = metric.compute(result)

        assert metric_result.value == 0.0
