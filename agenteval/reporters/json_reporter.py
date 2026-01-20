"""JSON reporter for machine-readable output."""

import json
from typing import Any, Dict

from agenteval.reporters.base import BaseReporter
from agenteval.schemas.execution import BenchmarkResult


class JSONReporter(BaseReporter):
    """
    Reporter that generates JSON output.

    Useful for:
    - Programmatic processing
    - Data pipelines
    - Long-term storage
    - Integration with other tools
    """

    def generate(self, result: BenchmarkResult) -> str:
        """
        Generate JSON report.

        Args:
            result: Benchmark result

        Returns:
            JSON string
        """
        # Convert result to dictionary
        report_dict = self._build_report_dict(result)

        # Pretty print if configured
        indent = self.config.get("indent", 2)
        ensure_ascii = self.config.get("ensure_ascii", False)

        return json.dumps(report_dict, indent=indent, ensure_ascii=ensure_ascii, default=str)

    def _build_report_dict(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Build report dictionary from benchmark result."""
        return {
            "benchmark": {
                "name": result.benchmark_name,
                "adapter": result.adapter_name,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "total_time": result.total_time,
            },
            "summary": {
                "total_tasks": result.total_tasks,
                "successful_tasks": result.successful_tasks,
                "failed_tasks": result.failed_tasks,
                "success_rate": result.success_rate,
                "average_execution_time": result.average_execution_time,
            },
            "token_usage": result.total_token_usage.model_dump() if result.total_token_usage else None,
            "cost": {
                "total_usd": result.total_cost,
                "average_per_task": result.total_cost / result.total_tasks if result.total_tasks > 0 else 0,
            },
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "success": task.success,
                    "execution_time": task.execution_time,
                    "token_usage": task.token_usage.model_dump() if task.token_usage else None,
                    "cost": task.cost,
                    "error": task.error,
                    "validation_passed": task.validation_passed,
                }
                for task in result.task_results
            ],
            "config": result.config,
            "metadata": result.metadata,
        }
