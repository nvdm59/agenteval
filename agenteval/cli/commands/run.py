"""Run benchmark command."""

import asyncio
import typer
from pathlib import Path
from typing import Optional, List

from agenteval.adapters import get_adapter, list_adapters
from agenteval.benchmarks import load_suite, load_task
from agenteval.executors import SequentialExecutor, ParallelExecutor
from agenteval.reporters import ConsoleReporter, JSONReporter
from agenteval.config import get_settings


def run_benchmark(
    benchmark: str = typer.Argument(..., help="Benchmark name or path to YAML file"),
    adapter: str = typer.Option(..., "--adapter", "-a", help="Adapter name (anthropic, openai, etc.)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name to use"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("console", "--format", "-f", help="Output format (console, json)"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Run tasks in parallel"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max concurrent tasks"),
    save_trace: bool = typer.Option(True, "--trace/--no-trace", help="Save execution traces"),
    timeout: int = typer.Option(300, "--timeout", "-t", help="Task timeout in seconds"),
):
    """
    Run a benchmark evaluation.

    Examples:
        # Run reasoning suite with Anthropic
        agenteval run reasoning --adapter anthropic

        # Run with specific model
        agenteval run my_benchmark.yaml --adapter openai --model gpt-4o

        # Save results to JSON
        agenteval run reasoning --adapter anthropic --output results.json --format json

        # Run in parallel
        agenteval run reasoning --adapter anthropic --parallel --concurrency 3
    """
    try:
        asyncio.run(_run_benchmark_async(
            benchmark=benchmark,
            adapter=adapter,
            model=model,
            output=output,
            format=format,
            parallel=parallel,
            concurrency=concurrency,
            save_trace=save_trace,
            timeout=timeout,
        ))
    except KeyboardInterrupt:
        typer.echo("\n⚠️  Interrupted by user")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


async def _run_benchmark_async(
    benchmark: str,
    adapter: str,
    model: Optional[str],
    output: Optional[Path],
    format: str,
    parallel: bool,
    concurrency: int,
    save_trace: bool,
    timeout: int,
):
    """Async implementation of benchmark run."""
    settings = get_settings()

    # Load benchmark
    typer.echo(f"📋 Loading benchmark: {benchmark}")
    benchmark_path = Path(benchmark)

    if benchmark_path.exists() and benchmark_path.suffix in [".yaml", ".yml"]:
        # Load from file
        if "suite" in benchmark_path.name:
            bench = load_suite(benchmark_path)
        else:
            task = load_task(benchmark_path)
            # Wrap single task
            from agenteval.schemas.benchmark import Benchmark, BenchmarkSuite

            bench = Benchmark(
                suite=BenchmarkSuite(
                    name=task.task_id, description=task.metadata.description, tasks=[]
                ),
                loaded_tasks=[task],
            )
    else:
        # Try to find in benchmarks directory
        bench_dir = Path("benchmarks") / benchmark
        suite_file = bench_dir / "suite.yaml"

        if suite_file.exists():
            bench = load_suite(suite_file)
        else:
            typer.echo(f"❌ Benchmark not found: {benchmark}", err=True)
            raise typer.Exit(1)

    typer.echo(f"✅ Loaded: {bench.suite.name} ({bench.task_count} tasks)")

    # Check adapter
    if adapter not in list_adapters():
        typer.echo(f"❌ Unknown adapter: {adapter}", err=True)
        typer.echo(f"   Available: {', '.join(list_adapters())}")
        raise typer.Exit(1)

    # Get API key
    api_key = settings.get_api_key(adapter)
    if not api_key:
        typer.echo(f"❌ API key not configured for {adapter}", err=True)
        typer.echo(f"   Set AGENTEVAL_{adapter.upper()}_API_KEY environment variable")
        raise typer.Exit(1)

    # Determine model
    if model is None:
        # Use defaults
        if adapter == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        elif adapter == "openai":
            model = "gpt-4o"
        else:
            typer.echo(f"❌ Model not specified for {adapter}", err=True)
            raise typer.Exit(1)

    typer.echo(f"🔧 Adapter: {adapter}/{model}")

    # Create adapter
    adapter_instance = get_adapter(
        adapter,
        config={
            "api_key": api_key,
            "model": model,
            "max_tokens": 4096,
        },
    )

    # Create executor
    if parallel:
        typer.echo(f"⚡ Execution mode: Parallel (concurrency: {concurrency})")
        executor = ParallelExecutor(
            config={"max_concurrency": concurrency, "save_traces": save_trace, "timeout": timeout}
        )
    else:
        typer.echo("⚡ Execution mode: Sequential")
        executor = SequentialExecutor(config={"save_traces": save_trace, "timeout": timeout})

    # Run benchmark
    typer.echo("\n" + "=" * 60)
    result = await executor.execute_benchmark(
        tasks=bench.loaded_tasks, adapter=adapter_instance, benchmark_name=bench.suite.name
    )

    # Generate report
    typer.echo("\n" + "=" * 60)
    typer.echo("📊 Generating report...")

    if format == "json":
        reporter = JSONReporter()
    else:
        reporter = ConsoleReporter()

    # Print to console
    if format == "console" or output is None:
        reporter.print(result)

    # Save to file if specified
    if output:
        reporter.save(result, output)
        typer.echo(f"\n💾 Report saved to: {output}")

    # Exit with appropriate code
    if result.failed_tasks > 0:
        raise typer.Exit(1)
