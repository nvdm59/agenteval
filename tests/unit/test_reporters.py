"""Unit tests for reporters."""

import pytest
import json
from datetime import datetime
from pathlib import Path

from agenteval.reporters import ConsoleReporter, JSONReporter
from agenteval.schemas.execution import (
    BenchmarkResult,
    ExecutionResult,
    ExecutionStatus,
    TokenUsage,
)


@pytest.fixture
def sample_benchmark_result():
    """Create a sample benchmark result for testing."""
    task1 = ExecutionResult(
        task_id="task1",
        status=ExecutionStatus.COMPLETED,
        success=True,
        start_time=datetime.now(),
        end_time=datetime.now(),
        execution_time=1.5,
        output="Result 1",
        token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        cost=0.001,
        adapter_name="test_adapter",
        validation_passed=True,
    )

    task2 = ExecutionResult(
        task_id="task2",
        status=ExecutionStatus.FAILED,
        success=False,
        start_time=datetime.now(),
        end_time=datetime.now(),
        execution_time=0.5,
        error="Test error",
        adapter_name="test_adapter",
        validation_passed=False,
    )

    return BenchmarkResult(
        benchmark_name="test_benchmark",
        start_time=datetime.now(),
        end_time=datetime.now(),
        total_time=2.0,
        task_results=[task1, task2],
        total_tasks=2,
        successful_tasks=1,
        failed_tasks=1,
        total_token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        total_cost=0.001,
        average_execution_time=1.0,
        adapter_name="test_adapter",
        config={},
    )


@pytest.mark.unit
class TestJSONReporter:
    """Test JSON reporter."""

    def test_generate_json(self, sample_benchmark_result):
        """Test JSON generation."""
        reporter = JSONReporter()
        output = reporter.generate(sample_benchmark_result)

        assert isinstance(output, str)

        # Parse JSON to verify it's valid
        data = json.loads(output)
        assert "benchmark" in data
        assert "summary" in data
        assert "tasks" in data

    def test_json_content(self, sample_benchmark_result):
        """Test JSON content structure."""
        reporter = JSONReporter()
        output = reporter.generate(sample_benchmark_result)
        data = json.loads(output)

        # Check benchmark info
        assert data["benchmark"]["name"] == "test_benchmark"
        assert data["benchmark"]["adapter"] == "test_adapter"

        # Check summary
        assert data["summary"]["total_tasks"] == 2
        assert data["summary"]["successful_tasks"] == 1
        assert data["summary"]["failed_tasks"] == 1
        assert data["summary"]["success_rate"] == 0.5

        # Check tasks
        assert len(data["tasks"]) == 2
        assert data["tasks"][0]["task_id"] == "task1"
        assert data["tasks"][0]["success"] is True
        assert data["tasks"][1]["task_id"] == "task2"
        assert data["tasks"][1]["success"] is False

    def test_save_to_file(self, sample_benchmark_result, tmp_path):
        """Test saving JSON to file."""
        reporter = JSONReporter()
        output_file = tmp_path / "report.json"

        reporter.save(sample_benchmark_result, output_file)

        assert output_file.exists()

        # Verify content
        with open(output_file) as f:
            data = json.load(f)
            assert data["benchmark"]["name"] == "test_benchmark"


@pytest.mark.unit
class TestConsoleReporter:
    """Test console reporter."""

    def test_generate_console(self, sample_benchmark_result):
        """Test console output generation."""
        reporter = ConsoleReporter()
        output = reporter.generate(sample_benchmark_result)

        assert isinstance(output, str)
        assert len(output) > 0

        # Check for key elements
        assert "test_benchmark" in output
        assert "Summary" in output
        assert "Task Details" in output

    def test_console_contains_metrics(self, sample_benchmark_result):
        """Test that console output contains metrics."""
        reporter = ConsoleReporter()
        output = reporter.generate(sample_benchmark_result)

        # Check for metrics
        assert "Total Tasks" in output
        assert "Successful" in output
        assert "Failed" in output
        assert "Success Rate" in output
        assert "Token Usage" in output
        assert "Total Cost" in output

    def test_console_shows_task_details(self, sample_benchmark_result):
        """Test that console output shows task details."""
        reporter = ConsoleReporter()
        output = reporter.generate(sample_benchmark_result)

        # Check for task info
        assert "task1" in output
        assert "task2" in output
        assert "Test error" in output  # Error message

    def test_console_shows_failed_tasks(self, sample_benchmark_result):
        """Test that console output highlights failed tasks."""
        reporter = ConsoleReporter()
        output = reporter.generate(sample_benchmark_result)

        # Check for failed tasks section
        assert "Failed Tasks" in output or "❌" in output

    def test_save_to_file(self, sample_benchmark_result, tmp_path):
        """Test saving console output to file."""
        reporter = ConsoleReporter()
        output_file = tmp_path / "report.txt"

        reporter.save(sample_benchmark_result, output_file)

        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "test_benchmark" in content


@pytest.mark.unit
class TestReporterBase:
    """Test base reporter functionality."""

    def test_print_does_not_raise(self, sample_benchmark_result):
        """Test that print method works without errors."""
        reporter = ConsoleReporter()

        # Should not raise any exceptions
        reporter.print(sample_benchmark_result)
