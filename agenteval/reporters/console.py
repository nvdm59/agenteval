"""Console reporter with rich formatting."""

from agenteval.reporters.base import BaseReporter
from agenteval.schemas.execution import BenchmarkResult, ExecutionStatus


class ConsoleReporter(BaseReporter):
    """
    Reporter that generates formatted console output.

    Useful for:
    - Interactive terminal sessions
    - Quick result viewing
    - CI/CD logs
    """

    def generate(self, result: BenchmarkResult) -> str:
        """
        Generate console report.

        Args:
            result: Benchmark result

        Returns:
            Formatted string for console output
        """
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append(f"  Benchmark Results: {result.benchmark_name}")
        lines.append("=" * 70)

        # Summary section
        lines.append("\n📊 Summary")
        lines.append("-" * 70)
        lines.append(f"Adapter:              {result.adapter_name}")
        lines.append(f"Total Time:           {result.total_time:.2f}s")
        lines.append(f"Average Task Time:    {result.average_execution_time:.2f}s")
        lines.append("")
        lines.append(f"Total Tasks:          {result.total_tasks}")
        lines.append(f"✅ Successful:        {result.successful_tasks}")
        lines.append(f"❌ Failed:            {result.failed_tasks}")
        lines.append(f"Success Rate:         {result.success_rate:.1%}")

        # Token usage
        if result.total_token_usage:
            lines.append("\n💰 Token Usage")
            lines.append("-" * 70)
            lines.append(f"Input Tokens:         {result.total_token_usage.input_tokens:,}")
            lines.append(f"Output Tokens:        {result.total_token_usage.output_tokens:,}")
            lines.append(f"Total Tokens:         {result.total_token_usage.total_tokens:,}")

        # Cost
        if result.total_cost:
            lines.append("")
            lines.append(f"Total Cost:           ${result.total_cost:.6f} USD")
            avg_cost = result.total_cost / result.total_tasks if result.total_tasks > 0 else 0
            lines.append(f"Average Cost/Task:    ${avg_cost:.6f} USD")

        # Task details
        lines.append("\n📝 Task Details")
        lines.append("-" * 70)

        for i, task in enumerate(result.task_results, 1):
            status_emoji = self._get_status_emoji(task.status, task.success)

            lines.append(f"\n{status_emoji} Task {i}: {task.task_id}")
            lines.append(f"   Status:        {task.status.value}")
            lines.append(f"   Success:       {task.success}")
            lines.append(f"   Time:          {task.execution_time:.2f}s")

            if task.token_usage:
                lines.append(f"   Tokens:        {task.token_usage.total_tokens:,}")

            if task.cost:
                lines.append(f"   Cost:          ${task.cost:.6f}")

            if task.validation_passed is not None:
                lines.append(f"   Validated:     {task.validation_passed}")

            if task.error:
                lines.append(f"   Error:         {task.error}")

        # Failed tasks section (if any)
        failed = result.get_failed_tasks()
        if failed:
            lines.append("\n⚠️  Failed Tasks")
            lines.append("-" * 70)
            for task in failed:
                lines.append(f"  • {task.task_id}: {task.error or 'Unknown error'}")

        # Footer
        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    def _get_status_emoji(self, status: ExecutionStatus, success: bool) -> str:
        """Get emoji for task status."""
        if status == ExecutionStatus.COMPLETED and success:
            return "✅"
        elif status == ExecutionStatus.COMPLETED:
            return "⚠️"
        elif status == ExecutionStatus.FAILED:
            return "❌"
        elif status == ExecutionStatus.TIMEOUT:
            return "⏱️"
        elif status == ExecutionStatus.CANCELLED:
            return "🚫"
        else:
            return "❓"
