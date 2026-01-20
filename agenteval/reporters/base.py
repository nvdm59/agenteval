"""Base reporter class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from agenteval.schemas.execution import BenchmarkResult


class BaseReporter(ABC):
    """
    Base class for all reporters.

    Reporters generate output from benchmark results in various formats
    (console, JSON, HTML, CSV, etc.).
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize reporter.

        Args:
            config: Optional configuration for reporter
        """
        self.config = config or {}

    @abstractmethod
    def generate(self, result: BenchmarkResult) -> str:
        """
        Generate report from benchmark result.

        Args:
            result: Benchmark result to report on

        Returns:
            Report content as string
        """
        pass

    def save(self, result: BenchmarkResult, output_path: Union[str, Path]) -> None:
        """
        Generate and save report to file.

        Args:
            result: Benchmark result
            output_path: Path to save report
        """
        content = self.generate(result)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def print(self, result: BenchmarkResult) -> None:
        """
        Generate and print report to stdout.

        Args:
            result: Benchmark result
        """
        content = self.generate(result)
        print(content)
