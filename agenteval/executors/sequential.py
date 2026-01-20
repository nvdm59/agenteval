"""Sequential task executor."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from agenteval.adapters.base import BaseAdapter
from agenteval.executors.base import BaseExecutor
from agenteval.schemas.benchmark import Task
from agenteval.schemas.execution import (
    BenchmarkResult,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)


class SequentialExecutor(BaseExecutor):
    """
    Executor that runs tasks sequentially, one at a time.

    This is the default and safest execution mode. It's useful when:
    - You want to carefully monitor each task
    - Tasks have dependencies on each other
    - You want to avoid rate limits
    - You're debugging or developing
    """

    async def execute_task(
        self, task: Task, adapter: BaseAdapter, context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute a single task.

        Args:
            task: Task to execute
            adapter: Adapter to use
            context: Optional execution context

        Returns:
            ExecutionResult
        """
        if context is None:
            context = self._create_context(task, adapter)

        # Execute with timeout protection
        result = await self._execute_with_timeout(task, adapter, context)

        return result

    async def execute_benchmark(
        self, tasks: List[Task], adapter: BaseAdapter, **kwargs
    ) -> BenchmarkResult:
        """
        Execute benchmark tasks sequentially.

        Args:
            tasks: List of tasks to execute
            adapter: Adapter to use
            **kwargs: Additional configuration
                - benchmark_name: Name of the benchmark
                - stop_on_failure: Stop if a task fails

        Returns:
            BenchmarkResult with aggregated results
        """
        benchmark_name = kwargs.get("benchmark_name", "unnamed_benchmark")
        stop_on_failure = kwargs.get("stop_on_failure", False)

        start_time = datetime.now()
        results: List[ExecutionResult] = []

        print(f"\n🚀 Starting sequential execution of {len(tasks)} tasks...")

        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Executing task: {task.task_id}")

            try:
                context = self._create_context(task, adapter)
                result = await self.execute_task(task, adapter, context)

                results.append(result)

                # Print result
                status_emoji = "✅" if result.is_successful else "❌"
                print(
                    f"{status_emoji} Task {task.task_id}: {result.status.value} "
                    f"(time: {result.execution_time:.2f}s)"
                )

                if result.token_usage:
                    print(f"   Tokens: {result.token_usage.total_tokens}")
                if result.cost:
                    print(f"   Cost: ${result.cost:.6f}")

                # Stop if configured and task failed
                if stop_on_failure and not result.is_successful:
                    print(f"\n⚠️  Stopping execution due to task failure: {task.task_id}")
                    break

            except Exception as e:
                print(f"❌ Error executing task {task.task_id}: {e}")
                # Create error result
                error_result = ExecutionResult(
                    task_id=task.task_id,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    execution_time=0.0,
                    error=str(e),
                    adapter_name=adapter.adapter_name,
                    validation_passed=False,
                )
                results.append(error_result)

                if stop_on_failure:
                    print(f"\n⚠️  Stopping execution due to error")
                    break

        # Aggregate results
        benchmark_result = self._aggregate_results(results, benchmark_name, start_time, adapter)

        print(f"\n✨ Benchmark complete!")
        print(f"   Total time: {benchmark_result.total_time:.2f}s")
        print(f"   Success rate: {benchmark_result.success_rate:.1%}")
        print(f"   Tasks: {benchmark_result.successful_tasks}/{benchmark_result.total_tasks}")
        if benchmark_result.total_cost:
            print(f"   Total cost: ${benchmark_result.total_cost:.6f}")

        return benchmark_result
