"""Main CLI application."""

import typer
from typing import Optional
from pathlib import Path

# Import command modules
from agenteval.cli.commands import run, list_cmd, validate

app = typer.Typer(
    name="agenteval",
    help="🤖 AgentEval - Evaluation framework for LLM-based agents",
    add_completion=False,
)

# Register commands
app.command(name="run", help="Run a benchmark evaluation")(run.run_benchmark)
app.command(name="list", help="List available resources")(list_cmd.list_resources)
app.command(name="validate", help="Validate a benchmark file")(validate.validate_benchmark)


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """
    AgentEval CLI - Evaluation framework for LLM-based agents.

    Use agenteval COMMAND --help for command-specific help.
    """
    if version:
        from agenteval.version import __version__

        typer.echo(f"AgentEval version {__version__}")
        raise typer.Exit()


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
