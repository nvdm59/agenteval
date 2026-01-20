"""Pydantic schemas for metrics."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics."""

    SUCCESS = "success"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    SAFETY = "safety"
    CUSTOM = "custom"


class MetricAggregation(str, Enum):
    """Methods for aggregating metrics."""

    MEAN = "mean"
    MEDIAN = "median"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTAGE = "percentage"


class MetricResult(BaseModel):
    """Result of a single metric computation."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    metric_type: MetricType = Field(..., description="Type of metric")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")

    # Context
    task_id: Optional[str] = Field(default=None, description="Task ID if metric is per-task")
    timestamp: datetime = Field(default_factory=datetime.now, description="Computation timestamp")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed breakdown of metric"
    )

    # Thresholds
    threshold: Optional[float] = Field(default=None, description="Threshold for pass/fail")
    passed: Optional[bool] = Field(default=None, description="Whether threshold was met")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "metric_type": self.metric_type.value,
            "unit": self.unit,
            "task_id": self.task_id,
            "metadata": self.metadata,
            "details": self.details,
            "threshold": self.threshold,
            "passed": self.passed,
        }


class MetricConfig(BaseModel):
    """Configuration for a metric."""

    name: str = Field(..., description="Metric name")
    enabled: bool = Field(default=True, description="Whether metric is enabled")
    metric_type: MetricType = Field(..., description="Type of metric")

    # Computation settings
    aggregation: MetricAggregation = Field(
        default=MetricAggregation.MEAN, description="Aggregation method"
    )
    threshold: Optional[float] = Field(default=None, description="Threshold value")

    # Additional settings
    config: Dict[str, Any] = Field(default_factory=dict, description="Metric-specific config")
    dependencies: List[str] = Field(
        default_factory=list, description="Other metrics this depends on"
    )


class MetricsSummary(BaseModel):
    """Summary of all metrics for a benchmark run."""

    benchmark_name: str = Field(..., description="Benchmark name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary timestamp")

    # Metrics by category
    success_metrics: List[MetricResult] = Field(
        default_factory=list, description="Success metrics"
    )
    efficiency_metrics: List[MetricResult] = Field(
        default_factory=list, description="Efficiency metrics"
    )
    quality_metrics: List[MetricResult] = Field(
        default_factory=list, description="Quality metrics"
    )
    safety_metrics: List[MetricResult] = Field(
        default_factory=list, description="Safety metrics"
    )
    custom_metrics: List[MetricResult] = Field(
        default_factory=list, description="Custom metrics"
    )

    # Overall statistics
    total_metrics: int = Field(default=0, description="Total number of metrics computed")
    thresholds_passed: int = Field(default=0, description="Number of thresholds passed")
    thresholds_failed: int = Field(default=0, description="Number of thresholds failed")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_metric(self, name: str) -> Optional[MetricResult]:
        """Get metric by name."""
        all_metrics = (
            self.success_metrics
            + self.efficiency_metrics
            + self.quality_metrics
            + self.safety_metrics
            + self.custom_metrics
        )
        for metric in all_metrics:
            if metric.name == name:
                return metric
        return None

    def get_metrics_by_type(self, metric_type: MetricType) -> List[MetricResult]:
        """Get all metrics of a specific type."""
        if metric_type == MetricType.SUCCESS:
            return self.success_metrics
        elif metric_type == MetricType.EFFICIENCY:
            return self.efficiency_metrics
        elif metric_type == MetricType.QUALITY:
            return self.quality_metrics
        elif metric_type == MetricType.SAFETY:
            return self.safety_metrics
        elif metric_type == MetricType.CUSTOM:
            return self.custom_metrics
        return []

    def get_failed_metrics(self) -> List[MetricResult]:
        """Get all metrics that failed their threshold."""
        all_metrics = (
            self.success_metrics
            + self.efficiency_metrics
            + self.quality_metrics
            + self.safety_metrics
            + self.custom_metrics
        )
        return [m for m in all_metrics if m.passed is False]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "timestamp": self.timestamp.isoformat(),
            "success_metrics": [m.to_dict() for m in self.success_metrics],
            "efficiency_metrics": [m.to_dict() for m in self.efficiency_metrics],
            "quality_metrics": [m.to_dict() for m in self.quality_metrics],
            "safety_metrics": [m.to_dict() for m in self.safety_metrics],
            "custom_metrics": [m.to_dict() for m in self.custom_metrics],
            "total_metrics": self.total_metrics,
            "thresholds_passed": self.thresholds_passed,
            "thresholds_failed": self.thresholds_failed,
            "metadata": self.metadata,
        }


class ComparisonResult(BaseModel):
    """Result of comparing metrics across multiple runs or adapters."""

    metric_name: str = Field(..., description="Metric being compared")
    runs: Dict[str, float] = Field(..., description="Metric values by run/adapter name")

    # Statistics
    best_value: float = Field(..., description="Best value")
    worst_value: float = Field(..., description="Worst value")
    mean_value: float = Field(..., description="Mean value")
    std_dev: Optional[float] = Field(default=None, description="Standard deviation")

    # Winner
    winner: str = Field(..., description="Name of best performing run/adapter")

    # Metadata
    metric_type: MetricType = Field(..., description="Type of metric")
    higher_is_better: bool = Field(default=True, description="Whether higher values are better")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MetricsComparison(BaseModel):
    """Comparison of metrics across multiple benchmark runs."""

    comparison_name: str = Field(..., description="Name of this comparison")
    timestamp: datetime = Field(default_factory=datetime.now, description="Comparison timestamp")

    # Runs being compared
    run_names: List[str] = Field(..., description="Names of runs being compared")

    # Comparisons by metric
    comparisons: List[ComparisonResult] = Field(
        default_factory=list, description="Metric comparisons"
    )

    # Overall winner
    overall_winner: Optional[str] = Field(
        default=None, description="Overall best performing run"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_comparison(self, metric_name: str) -> Optional[ComparisonResult]:
        """Get comparison for a specific metric."""
        for comp in self.comparisons:
            if comp.metric_name == metric_name:
                return comp
        return None

    def get_winner_count(self) -> Dict[str, int]:
        """Count how many metrics each run won."""
        counts = {name: 0 for name in self.run_names}
        for comp in self.comparisons:
            counts[comp.winner] += 1
        return counts
