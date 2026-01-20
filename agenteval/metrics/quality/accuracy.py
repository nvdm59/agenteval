"""Accuracy metrics for quality evaluation."""

from typing import Optional
from agenteval.metrics.base import BaseMetric, MetricRegistry
from agenteval.schemas.execution import ExecutionResult
from agenteval.schemas.metrics import MetricResult, MetricType


@MetricRegistry.register(
    "accuracy",
    description="Exact match accuracy between output and expected result",
    metric_type=MetricType.QUALITY,
)
class AccuracyMetric(BaseMetric):
    """
    Metric that checks if output matches expected result exactly.

    Useful for tasks with deterministic correct answers.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is a quality metric."""
        return MetricType.QUALITY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute accuracy by comparing output to expected result.

        Args:
            result: Execution result

        Returns:
            MetricResult with 1.0 for match, 0.0 for mismatch
        """
        # Get expected output from metadata (if task provided it)
        expected = result.metadata.get("expected_output")

        if expected is None:
            return MetricResult(
                name="accuracy",
                value=0.0,
                metric_type=self.metric_type,
                unit="score",
                task_id=result.task_id,
                metadata={"warning": "No expected output provided"},
            )

        # Compare output
        actual = str(result.output).strip()
        expected_str = str(expected).strip()

        # Case-insensitive comparison
        case_sensitive = self.config.get("case_sensitive", False)
        if not case_sensitive:
            actual = actual.lower()
            expected_str = expected_str.lower()

        match = actual == expected_str

        return MetricResult(
            name="accuracy",
            value=1.0 if match else 0.0,
            metric_type=self.metric_type,
            unit="score",
            task_id=result.task_id,
            metadata={
                "expected": expected_str,
                "actual": actual,
                "match": match,
            },
        )

    def get_unit(self) -> str:
        """Unit is score (0.0 to 1.0)."""
        return "score"


@MetricRegistry.register(
    "fuzzy_match",
    description="Fuzzy string matching for approximate accuracy",
    metric_type=MetricType.QUALITY,
)
class FuzzyMatchMetric(BaseMetric):
    """
    Metric that uses fuzzy string matching for approximate accuracy.

    Useful when exact matches are too strict.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is a quality metric."""
        return MetricType.QUALITY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute fuzzy match score.

        Args:
            result: Execution result

        Returns:
            MetricResult with similarity score (0.0 to 1.0)
        """
        expected = result.metadata.get("expected_output")

        if expected is None:
            return MetricResult(
                name="fuzzy_match",
                value=0.0,
                metric_type=self.metric_type,
                unit="score",
                task_id=result.task_id,
                metadata={"warning": "No expected output provided"},
            )

        actual = str(result.output).strip().lower()
        expected_str = str(expected).strip().lower()

        # Simple fuzzy matching using character overlap
        # (In production, use difflib or fuzzywuzzy library)
        if not expected_str:
            return MetricResult(
                name="fuzzy_match",
                value=0.0,
                metric_type=self.metric_type,
                unit="score",
                task_id=result.task_id,
            )

        # Calculate similarity based on common characters
        common = sum(1 for c in expected_str if c in actual)
        similarity = common / len(expected_str)

        return MetricResult(
            name="fuzzy_match",
            value=similarity,
            metric_type=self.metric_type,
            unit="score",
            task_id=result.task_id,
            metadata={
                "expected": expected_str,
                "actual": actual,
                "similarity": similarity,
            },
        )

    def get_unit(self) -> str:
        """Unit is score (0.0 to 1.0)."""
        return "score"


@MetricRegistry.register(
    "output_length",
    description="Length of agent output in characters",
    metric_type=MetricType.QUALITY,
)
class OutputLengthMetric(BaseMetric):
    """
    Metric that measures output length.

    Useful for checking if agent provides sufficient detail.
    """

    @property
    def metric_type(self) -> MetricType:
        """This is a quality metric."""
        return MetricType.QUALITY

    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute output length.

        Args:
            result: Execution result

        Returns:
            MetricResult with character count
        """
        output = str(result.output) if result.output else ""
        length = len(output)

        # Check against thresholds if provided
        min_length = self.config.get("min_length")
        max_length = self.config.get("max_length")

        passed: Optional[bool] = None
        if min_length is not None and max_length is not None:
            passed = min_length <= length <= max_length
        elif min_length is not None:
            passed = length >= min_length
        elif max_length is not None:
            passed = length <= max_length

        return MetricResult(
            name="output_length",
            value=float(length),
            metric_type=self.metric_type,
            unit="characters",
            task_id=result.task_id,
            passed=passed,
            threshold=min_length if min_length else max_length,
            metadata={
                "min_expected": min_length,
                "max_expected": max_length,
                "word_count": len(output.split()) if output else 0,
            },
        )

    def get_unit(self) -> str:
        """Unit is characters."""
        return "characters"
