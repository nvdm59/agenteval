"""Parallel task executor with concurrency control."""

import asyncio
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


class ParallelExecutor(BaseExecutor):
    """
    Executor that runs tasks in parallel with concurrency control.

    This executor uses asyncio to run multiple tasks concurrently,
    with a semaphore to limit the maximum number of concurrent tasks.

    Use this when:
    - Tasks are independent of each other
    - You want faster execution for large benchmarks
    - API rate limits allow parallel requests
    - You're running final evaluations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parallel executor.

        Args:
            config: Configuration with additional option:
                - max_concurrency: Maximum concurrent tasks (default: 5)
        """
        super().__init__(config)
        self.max_concurrency = self.config.get("max_concurrency", self.settings.max_concurrency)
        self.semaphore = asyncio.Semaphore(self.max_concurrency)

    async def execute_task(
        self, task: Task, adapter: BaseAdapter, context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute a single task with concurrency control.

        Args:
            task: Task to execute
            adapter: Adapter to use
            context: Optional execution context

        Returns:
            ExecutionResult
        """
        async with self.semaphore:
            if context is None:
                context = self._create_context(task, adapter)

            result = await self._execute_with_timeout(task, adapter, context)
            return result

    async def execute_benchmark(
        self, tasks: List[Task], adapter: BaseAdapter, **kwargs
    ) -> BenchmarkResult:
        """
        Execute benchmark tasks in parallel.

        Args:
            tasks: List of tasks to execute
            adapter: Adapter to use
            **kwargs: Additional configuration
                - benchmark_name: Name of the benchmark

        Returns:
            BenchmarkResult with aggregated results
        """
        benchmark_name = kwargs.get("benchmark_name", "unnamed_benchmark")

        start_time = datetime.now()

        print(
            f"\n🚀 Starting parallel execution of {len(tasks)} tasks "
            f"(max concurrency: {self.max_concurrency})..."
        )

        # Create tasks with progress tracking
        async def execute_with_progress(task: Task, task_num: int) -> ExecutionResult:
            """Execute task and print progress."""
            print(f"[{task_num}/{len(tasks)}] Starting task: {task.task_id}")

            try:
                context = self._create_context(task, adapter)
                result = await self.execute_task(task, adapter, context)

                status_emoji = "✅" if result.is_successful else "❌"
                print(
                    f"{status_emoji} [{task_num}/{len(tasks)}] Task {task.task_id}: "
                    f"{result.status.value} (time: {result.execution_time:.2f}s)"
                )

                return result

            except Exception as e:
                print(f"❌ [{task_num}/{len(tasks)}] Error in task {task.task_id}: {e}")
                return ExecutionResult(
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

        # Execute all tasks in parallel
        coroutines = [execute_with_progress(task, i + 1) for i, task in enumerate(tasks)]

        # Gather results, continuing even if some fail
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert any exceptions to error results
        processed_results: List[ExecutionResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Unexpected error in task {tasks[i].task_id}: {result}")
                processed_results.append(
                    ExecutionResult(
                        task_id=tasks[i].task_id,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        start_time=start_time,
                        end_time=datetime.now(),
                        execution_time=0.0,
                        error=str(result),
                        adapter_name=adapter.adapter_name,
                        validation_passed=False,
                    )
                )
            else:
                processed_results.append(result)

        # Aggregate results
        benchmark_result = self._aggregate_results(
            processed_results, benchmark_name, start_time, adapter
        )

        print(f"\n✨ Parallel benchmark complete!")
        print(f"   Total time: {benchmark_result.total_time:.2f}s")
        print(f"   Success rate: {benchmark_result.success_rate:.1%}")
        print(f"   Tasks: {benchmark_result.successful_tasks}/{benchmark_result.total_tasks}")
        if benchmark_result.total_cost:
            print(f"   Total cost: ${benchmark_result.total_cost:.6f}")
        print(
            f"   Average task time: {benchmark_result.average_execution_time:.2f}s "
            f"(with {self.max_concurrency}x concurrency)"
        )

        return benchmark_result

    async def execute_benchmark_batched(
        self, tasks: List[Task], adapter: BaseAdapter, batch_size: int = 10, **kwargs
    ) -> BenchmarkResult:
        """
        Execute benchmark in batches for very large benchmarks.

        This is useful when you have hundreds of tasks and want to
        process them in controlled batches.

        Args:
            tasks: List of tasks to execute
            adapter: Adapter to use
            batch_size: Number of tasks per batch
            **kwargs: Additional configuration

        Returns:
            BenchmarkResult with aggregated results
        """
        benchmark_name = kwargs.get("benchmark_name", "unnamed_benchmark")
        start_time = datetime.now()

        print(
            f"\n🚀 Starting batched parallel execution of {len(tasks)} tasks "
            f"(batch size: {batch_size})..."
        )

        all_results: List[ExecutionResult] = []

        # Process in batches
        for batch_num, i in enumerate(range(0, len(tasks), batch_size), 1):
            batch = tasks[i : i + batch_size]
            print(
                f"\n📦 Processing batch {batch_num}/{(len(tasks) + batch_size - 1) // batch_size}"
            )

            # Execute batch
            batch_results = await self.execute_benchmark(
                batch, adapter, benchmark_name=f"{benchmark_name}_batch_{batch_num}"
            )
            all_results.extend(batch_results.task_results)

        # Aggregate all results
        benchmark_result = self._aggregate_results(all_results, benchmark_name, start_time, adapter)

        print(f"\n✨ Batched benchmark complete!")
        print(f"   Total time: {benchmark_result.total_time:.2f}s")
        print(f"   Success rate: {benchmark_result.success_rate:.1%}")
        print(f"   Tasks: {benchmark_result.successful_tasks}/{benchmark_result.total_tasks}")
        if benchmark_result.total_cost:
            print(f"   Total cost: ${benchmark_result.total_cost:.6f}")

        return benchmark_result
