"""List command for available resources."""

import typer
from pathlib import Path
from typing import Optional, List

from agenteval.adapters import list_adapters, AdapterRegistry
from agenteval.metrics import list_metrics, MetricRegistry


def list_resources(
    resource_type: str = typer.Argument("benchmarks", help="What to list (benchmarks, metrics, adapters)"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Filter by tags"),
):
    """
    List available benchmarks, metrics, or adapters.

    Examples:
        # List all adapters
        agenteval list adapters

        # List all metrics
        agenteval list metrics

        # List benchmarks
        agenteval list benchmarks
    """
    resource_type = resource_type.lower()

    if resource_type in ["adapter", "adapters"]:
        _list_adapters()
    elif resource_type in ["metric", "metrics"]:
        _list_metrics()
    elif resource_type in ["benchmark", "benchmarks"]:
        _list_benchmarks(tags=tag)
    else:
        typer.echo(f"❌ Unknown resource type: {resource_type}", err=True)
        typer.echo("   Valid types: benchmarks, metrics, adapters")
        raise typer.Exit(1)


def _list_adapters():
    """List all available adapters."""
    adapters = list_adapters()

    typer.echo("\n🔌 Available Adapters")
    typer.echo("=" * 60)

    if not adapters:
        typer.echo("No adapters found.")
        return

    for adapter_name in sorted(adapters):
        info = AdapterRegistry.get_adapter_info(adapter_name)

        typer.echo(f"\n📦 {adapter_name}")
        if info.get("description"):
            typer.echo(f"   {info['description']}")

        features = []
        if info.get("supports_tools"):
            features.append("✅ Tool calling")
        if info.get("supports_streaming"):
            features.append("✅ Streaming")

        if features:
            typer.echo(f"   {' | '.join(features)}")

    typer.echo("")


def _list_metrics():
    """List all available metrics."""
    metrics = list_metrics()

    typer.echo("\n📊 Available Metrics")
    typer.echo("=" * 60)

    if not metrics:
        typer.echo("No metrics found.")
        return

    # Group by type
    from agenteval.schemas.metrics import MetricType

    metrics_by_type = {
        MetricType.SUCCESS: [],
        MetricType.EFFICIENCY: [],
        MetricType.QUALITY: [],
        MetricType.SAFETY: [],
        MetricType.CUSTOM: [],
    }

    for metric_name in sorted(metrics):
        info = MetricRegistry.get_metric_info(metric_name)
        metric_type_str = info.get("metric_type")

        if metric_type_str:
            metric_type = MetricType(metric_type_str)
            metrics_by_type[metric_type].append((metric_name, info))

    # Display by type
    for metric_type, metric_list in metrics_by_type.items():
        if not metric_list:
            continue

        typer.echo(f"\n{metric_type.value.upper()} Metrics:")
        typer.echo("-" * 60)

        for metric_name, info in metric_list:
            typer.echo(f"  • {metric_name}")
            if info.get("description"):
                typer.echo(f"    {info['description']}")

    typer.echo("")


def _list_benchmarks(tags: Optional[List[str]] = None):
    """List available benchmarks."""
    typer.echo("\n📋 Available Benchmarks")
    typer.echo("=" * 60)

    # Look for benchmarks in benchmarks directory
    benchmarks_dir = Path("benchmarks")

    if not benchmarks_dir.exists():
        typer.echo("No benchmarks directory found.")
        typer.echo("Create benchmarks in ./benchmarks/")
        return

    found_suites = []

    # Find all suite.yaml files
    for suite_file in benchmarks_dir.rglob("suite.yaml"):
        suite_name = suite_file.parent.name
        found_suites.append((suite_name, suite_file))

    # Find individual task files
    individual_tasks = []
    for yaml_file in benchmarks_dir.rglob("*.yaml"):
        if yaml_file.name != "suite.yaml":
            individual_tasks.append(yaml_file)

    # Display suites
    if found_suites:
        typer.echo("\nBenchmark Suites:")
        typer.echo("-" * 60)

        for suite_name, suite_file in sorted(found_suites):
            typer.echo(f"  📦 {suite_name}")
            typer.echo(f"     Path: {suite_file.relative_to(benchmarks_dir.parent)}")

            # Try to load and show task count
            try:
                from agenteval.benchmarks import load_suite

                suite = load_suite(suite_file)
                typer.echo(f"     Tasks: {suite.task_count}")
                if suite.suite.description:
                    typer.echo(f"     {suite.suite.description}")
            except Exception:
                pass

    # Display individual tasks
    if individual_tasks:
        typer.echo("\nIndividual Tasks:")
        typer.echo("-" * 60)

        for task_file in sorted(individual_tasks):
            task_name = task_file.stem
            typer.echo(f"  📄 {task_name}")
            typer.echo(f"     Path: {task_file.relative_to(benchmarks_dir.parent)}")

    if not found_suites and not individual_tasks:
        typer.echo("\nNo benchmarks found.")
        typer.echo("Create benchmark YAML files in ./benchmarks/")

    typer.echo("")
