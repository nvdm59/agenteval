"""Validate benchmark command."""

import typer
from pathlib import Path

from agenteval.benchmarks import BenchmarkLoader


def validate_benchmark(
    benchmark_file: Path = typer.Argument(..., help="Path to benchmark YAML file"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict validation"),
):
    """
    Validate a benchmark definition file.

    Examples:
        # Validate a task file
        agenteval validate benchmarks/reasoning/simple_math.yaml

        # Validate with strict mode
        agenteval validate my_benchmark.yaml --strict
    """
    if not benchmark_file.exists():
        typer.echo(f"❌ File not found: {benchmark_file}", err=True)
        raise typer.Exit(1)

    if benchmark_file.suffix not in [".yaml", ".yml"]:
        typer.echo(f"❌ File must be YAML (.yaml or .yml): {benchmark_file}", err=True)
        raise typer.Exit(1)

    typer.echo(f"🔍 Validating: {benchmark_file}")
    typer.echo("")

    try:
        # Try to load as suite first
        if "suite" in benchmark_file.name:
            typer.echo("📦 Detected as benchmark suite")
            benchmark = BenchmarkLoader.load_suite(benchmark_file)

            typer.echo(f"✅ Suite loaded successfully!")
            typer.echo(f"   Name: {benchmark.suite.name}")
            typer.echo(f"   Description: {benchmark.suite.description}")
            typer.echo(f"   Tasks: {benchmark.task_count}")

            # Validate each task
            typer.echo("\n   Task validation:")
            for task in benchmark.loaded_tasks:
                typer.echo(f"     ✅ {task.task_id}")

        else:
            # Load as single task
            typer.echo("📄 Detected as single task")
            task = BenchmarkLoader.load_task(benchmark_file)

            typer.echo(f"✅ Task loaded successfully!")
            typer.echo(f"   Name: {task.metadata.name}")
            typer.echo(f"   Description: {task.metadata.description}")
            typer.echo(f"   Type: {task.task.type.value}")
            typer.echo(f"   Difficulty: {task.metadata.difficulty.value}")

            # Validation details
            typer.echo("\n   Validation:")
            typer.echo(f"     Method: {task.task.validation.method.value}")
            typer.echo(f"     Success criteria: {len(task.task.success_criteria)}")

            if task.task.tools:
                typer.echo(f"     Tools: {len(task.task.tools)}")

            if task.task.expected_output:
                typer.echo(f"     Expected output: ✅ Defined")

        # Strict validation checks
        if strict:
            typer.echo("\n🔬 Strict validation checks:")

            checks_passed = 0
            checks_total = 0

            # Check 1: Instructions not empty
            checks_total += 1
            if "instructions" in str(benchmark_file.read_text()):
                typer.echo("  ✅ Has instructions")
                checks_passed += 1
            else:
                typer.echo("  ❌ Missing instructions")

            # Check 2: Has success criteria
            checks_total += 1
            if "success_criteria" in str(benchmark_file.read_text()):
                typer.echo("  ✅ Has success criteria")
                checks_passed += 1
            else:
                typer.echo("  ⚠️  No success criteria defined")

            # Check 3: Has validation method
            checks_total += 1
            if "validation" in str(benchmark_file.read_text()):
                typer.echo("  ✅ Has validation method")
                checks_passed += 1
            else:
                typer.echo("  ❌ Missing validation method")

            typer.echo(f"\n   Passed {checks_passed}/{checks_total} strict checks")

            if checks_passed < checks_total:
                typer.echo("\n⚠️  Some strict validation checks failed")
                raise typer.Exit(1)

        typer.echo("\n✅ Validation successful!")

    except Exception as e:
        typer.echo(f"\n❌ Validation failed!", err=True)
        typer.echo(f"   Error: {e}", err=True)
        raise typer.Exit(1)
