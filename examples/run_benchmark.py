"""
Example of running a complete benchmark suite.

This example demonstrates:
1. Loading a benchmark suite from YAML
2. Setting up an adapter
3. Running the benchmark with an executor
4. Viewing aggregated results
"""

import asyncio
import os
from pathlib import Path

from agenteval.adapters import get_adapter
from agenteval.benchmarks import load_suite
from agenteval.executors import SequentialExecutor, ParallelExecutor


async def main():
    """Run a complete benchmark suite."""

    print("=" * 60)
    print("  AgentEval - Benchmark Suite Example")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("AGENTEVAL_ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ Error: AGENTEVAL_ANTHROPIC_API_KEY environment variable not set")
        print("   Please set it with: export AGENTEVAL_ANTHROPIC_API_KEY=your-key-here")
        return

    # Step 1: Load benchmark suite
    print("\n📋 Step 1: Loading benchmark suite...")

    # Get path to reasoning suite
    current_dir = Path(__file__).parent.parent
    suite_path = current_dir / "benchmarks" / "reasoning" / "suite.yaml"

    if not suite_path.exists():
        print(f"❌ Suite file not found: {suite_path}")
        return

    try:
        benchmark = load_suite(suite_path)
        print(f"✅ Loaded suite: {benchmark.suite.name}")
        print(f"   Description: {benchmark.suite.description}")
        print(f"   Tasks: {benchmark.task_count}")

        for task in benchmark.loaded_tasks:
            print(f"   - {task.task_id}: {task.metadata.description}")

    except Exception as e:
        print(f"❌ Error loading suite: {e}")
        return

    # Step 2: Set up adapter
    print("\n🔧 Step 2: Setting up adapter...")

    adapter = get_adapter(
        "anthropic",
        config={
            "api_key": api_key,
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "temperature": 0.0,  # Deterministic for benchmarking
        },
    )

    print(f"✅ Adapter configured: {adapter.adapter_name}")

    # Step 3: Choose executor
    print("\n⚙️  Step 3: Choose executor mode...")
    print("   1. Sequential (slower, safer)")
    print("   2. Parallel (faster, uses concurrency)")

    # For this example, use sequential
    use_parallel = False  # Change to True to use parallel executor

    if use_parallel:
        executor = ParallelExecutor(config={"max_concurrency": 3, "save_traces": True})
        print("   Selected: Parallel execution")
    else:
        executor = SequentialExecutor(config={"save_traces": True})
        print("   Selected: Sequential execution")

    # Step 4: Run benchmark
    print("\n🏃 Step 4: Running benchmark...")
    print("-" * 60)

    try:
        result = await executor.execute_benchmark(
            tasks=benchmark.loaded_tasks,
            adapter=adapter,
            benchmark_name=benchmark.suite.name,
        )

        # Step 5: Display results
        print("\n" + "=" * 60)
        print("  Benchmark Results")
        print("=" * 60)

        print(f"\n📊 Overall Statistics:")
        print(f"   Total Tasks: {result.total_tasks}")
        print(f"   Successful: {result.successful_tasks}")
        print(f"   Failed: {result.failed_tasks}")
        print(f"   Success Rate: {result.success_rate:.1%}")
        print(f"   Total Time: {result.total_time:.2f}s")
        print(f"   Average Task Time: {result.average_execution_time:.2f}s")

        if result.total_token_usage:
            print(f"\n💰 Token Usage:")
            print(f"   Input Tokens: {result.total_token_usage.input_tokens:,}")
            print(f"   Output Tokens: {result.total_token_usage.output_tokens:,}")
            print(f"   Total Tokens: {result.total_token_usage.total_tokens:,}")

        if result.total_cost:
            print(f"   Estimated Cost: ${result.total_cost:.6f} USD")

        print(f"\n📝 Task Details:")
        for task_result in result.task_results:
            status_emoji = "✅" if task_result.is_successful else "❌"
            print(f"\n   {status_emoji} {task_result.task_id}")
            print(f"      Status: {task_result.status.value}")
            print(f"      Time: {task_result.execution_time:.2f}s")
            if task_result.token_usage:
                print(f"      Tokens: {task_result.token_usage.total_tokens}")
            if task_result.cost:
                print(f"      Cost: ${task_result.cost:.6f}")

            if not task_result.is_successful and task_result.error:
                print(f"      Error: {task_result.error}")

        # Show failed tasks if any
        failed = result.get_failed_tasks()
        if failed:
            print(f"\n⚠️  Failed Tasks ({len(failed)}):")
            for fail in failed:
                print(f"   - {fail.task_id}: {fail.error or 'Unknown error'}")

        print("\n" + "=" * 60)
        print("✨ Benchmark complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running benchmark: {e}")
        import traceback

        traceback.print_exc()
        return


if __name__ == "__main__":
    asyncio.run(main())
