"""Base metric class and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from agenteval.schemas.execution import ExecutionResult
from agenteval.schemas.metrics import MetricResult, MetricType


class BaseMetric(ABC):
    """
    Base class for all evaluation metrics.

    Metrics compute specific measurements from execution results,
    such as success rate, token usage, cost, quality scores, etc.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize metric.

        Args:
            config: Optional configuration for metric computation
        """
        self.config = config or {}
        self.name = self.__class__.__name__.replace("Metric", "").lower()

    @abstractmethod
    def compute(self, result: ExecutionResult) -> MetricResult:
        """
        Compute metric from execution result.

        Args:
            result: Execution result to compute metric from

        Returns:
            MetricResult with computed value
        """
        pass

    @property
    @abstractmethod
    def metric_type(self) -> MetricType:
        """
        Get the type of this metric.

        Returns:
            MetricType enum value
        """
        pass

    def aggregate(self, results: List[MetricResult]) -> MetricResult:
        """
        Aggregate multiple metric results.

        Default implementation computes the mean.
        Override for custom aggregation logic.

        Args:
            results: List of metric results to aggregate

        Returns:
            Aggregated metric result
        """
        if not results:
            return MetricResult(
                name=self.name, value=0.0, metric_type=self.metric_type, unit=self.get_unit()
            )

        total = sum(r.value for r in results)
        mean = total / len(results)

        return MetricResult(
            name=self.name,
            value=mean,
            metric_type=self.metric_type,
            unit=self.get_unit(),
            metadata={"count": len(results), "min": min(r.value for r in results), "max": max(r.value for r in results)},
        )

    def get_unit(self) -> Optional[str]:
        """
        Get the unit for this metric.

        Returns:
            Unit string (e.g., "seconds", "tokens", "USD") or None
        """
        return None

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}()"


class MetricRegistry:
    """
    Registry for managing metrics.

    Allows for discovery and instantiation of metrics by name.
    """

    _metrics: Dict[str, Type[BaseMetric]] = {}
    _metadata: Dict[str, Dict] = {}

    @classmethod
    def register(
        cls, name: str, description: str = "", metric_type: Optional[MetricType] = None
    ):
        """
        Decorator to register a metric.

        Args:
            name: Unique name for the metric
            description: Human-readable description
            metric_type: Type of metric

        Returns:
            Decorator function

        Example:
            @MetricRegistry.register("completion_rate", metric_type=MetricType.SUCCESS)
            class CompletionRateMetric(BaseMetric):
                ...
        """

        def decorator(metric_class: Type[BaseMetric]):
            if name in cls._metrics:
                raise ValueError(f"Metric '{name}' is already registered")

            if not issubclass(metric_class, BaseMetric):
                raise TypeError(f"Metric must be a subclass of BaseMetric")

            cls._metrics[name] = metric_class
            cls._metadata[name] = {
                "name": name,
                "class_name": metric_class.__name__,
                "description": description,
                "metric_type": metric_type.value if metric_type else None,
            }
            return metric_class

        return decorator

    @classmethod
    def get_metric(cls, name: str, config: Optional[Dict] = None) -> BaseMetric:
        """
        Get metric instance by name.

        Args:
            name: Metric name
            config: Optional configuration

        Returns:
            Instantiated metric

        Raises:
            ValueError: If metric name is not registered
        """
        if name not in cls._metrics:
            available = ", ".join(cls._metrics.keys())
            raise ValueError(f"Unknown metric: '{name}'. Available metrics: {available}")

        metric_class = cls._metrics[name]
        return metric_class(config)

    @classmethod
    def list_metrics(cls) -> List[str]:
        """
        List all registered metric names.

        Returns:
            List of metric names
        """
        return list(cls._metrics.keys())

    @classmethod
    def get_metric_info(cls, name: str) -> Dict:
        """
        Get metadata for a specific metric.

        Args:
            name: Metric name

        Returns:
            Dictionary with metric metadata

        Raises:
            ValueError: If metric name is not registered
        """
        if name not in cls._metadata:
            raise ValueError(f"Unknown metric: '{name}'")

        return cls._metadata[name].copy()

    @classmethod
    def get_all_metric_info(cls) -> Dict[str, Dict]:
        """
        Get metadata for all registered metrics.

        Returns:
            Dictionary mapping metric names to their metadata
        """
        return cls._metadata.copy()

    @classmethod
    def get_metrics_by_type(cls, metric_type: MetricType) -> List[str]:
        """
        Get all metrics of a specific type.

        Args:
            metric_type: Type of metrics to get

        Returns:
            List of metric names of that type
        """
        return [
            name
            for name, meta in cls._metadata.items()
            if meta.get("metric_type") == metric_type.value
        ]


# Convenience function
def get_metric(name: str, config: Optional[Dict] = None) -> BaseMetric:
    """
    Convenience function to get a metric instance.

    Args:
        name: Metric name
        config: Optional configuration

    Returns:
        Instantiated metric
    """
    return MetricRegistry.get_metric(name, config)


def list_metrics() -> List[str]:
    """
    Convenience function to list available metrics.

    Returns:
        List of metric names
    """
    return MetricRegistry.list_metrics()
