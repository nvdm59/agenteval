"""End-to-end integration tests."""

import pytest
import os
from pathlib import Path

from agenteval.adapters import get_adapter
from agenteval.benchmarks import load_from_dict
from agenteval.executors import SequentialExecutor
from agenteval.metrics import get_metric
from agenteval.reporters import JSONReporter, ConsoleReporter


@pytest.mark.integration
@pytest.mark.requires_api
class TestEndToEnd:
    """Integration tests requiring API keys."""

    @pytest.fixture
    def has_anthropic_key(self):
        """Check if Anthropic API key is available."""
        return os.getenv("AGENTEVAL_ANTHROPIC_API_KEY") is not None

    @pytest.fixture
    def simple_task(self):
        """Create a simple test task."""
        return load_from_dict(
            {
                "metadata": {
                    "name": "simple_test",
                    "description": "Simple integration test",
                    "tags": ["test"],
                },
                "task": {
                    "type": "reasoning",
                    "instructions": "What is 2 + 2? Provide just the number.",
                    "success_criteria": [
                        {"type": "output_contains", "value": "4", "required": True}
                    ],
                    "validation": {"method": "rule_based"},
                },
            }
        )

    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self, simple_task, has_anthropic_key):
        """Test complete evaluation workflow."""
        if not has_anthropic_key:
            pytest.skip("Anthropic API key not available")

        # Setup adapter
        adapter = get_adapter(
            "anthropic",
            config={
                "api_key": os.getenv("AGENTEVAL_ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
            },
        )

        # Setup executor
        executor = SequentialExecutor(config={"save_traces": False})

        # Run benchmark
        result = await executor.execute_benchmark(
            tasks=[simple_task], adapter=adapter, benchmark_name="integration_test"
        )

        # Verify result
        assert result.total_tasks == 1
        assert result.successful_tasks >= 0
        assert result.total_token_usage is not None
        assert result.total_cost is not None
        assert result.total_cost > 0

        # Test metrics
        completion_metric = get_metric("completion_rate")
        token_metric = get_metric("token_usage")

        for task_result in result.task_results:
            completion = completion_metric.compute(task_result)
            tokens = token_metric.compute(task_result)

            assert completion.value in [0.0, 1.0]
            assert tokens.value >= 0

        # Test reporters
        json_reporter = JSONReporter()
        json_output = json_reporter.generate(result)
        assert len(json_output) > 0

        console_reporter = ConsoleReporter()
        console_output = console_reporter.generate(result)
        assert len(console_output) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, has_anthropic_key):
        """Test error handling in execution."""
        if not has_anthropic_key:
            pytest.skip("Anthropic API key not available")

        # Create task with very short timeout
        task = load_from_dict(
            {
                "metadata": {"name": "timeout_test", "description": "Test timeout"},
                "task": {
                    "type": "general",
                    "instructions": "This is a test",
                    "validation": {"method": "rule_based"},
                },
            }
        )

        adapter = get_adapter(
            "anthropic",
            config={
                "api_key": os.getenv("AGENTEVAL_ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022",
            },
        )

        executor = SequentialExecutor(config={"timeout": 0.001})  # Very short timeout

        result = await executor.execute_benchmark(
            tasks=[task], adapter=adapter, benchmark_name="timeout_test"
        )

        # Should complete but possibly with errors
        assert result.total_tasks == 1


@pytest.mark.integration
class TestBenchmarkLoading:
    """Integration tests for benchmark loading."""

    def test_load_existing_benchmarks(self):
        """Test loading existing benchmark files."""
        benchmarks_dir = Path("benchmarks")

        if not benchmarks_dir.exists():
            pytest.skip("Benchmarks directory not found")

        # Look for suite files
        suite_files = list(benchmarks_dir.rglob("suite.yaml"))

        if suite_files:
            from agenteval.benchmarks import load_suite

            for suite_file in suite_files:
                try:
                    suite = load_suite(suite_file)
                    assert suite.task_count > 0
                    assert len(suite.suite.name) > 0
                except Exception as e:
                    pytest.fail(f"Failed to load {suite_file}: {e}")


@pytest.mark.integration
class TestMetricsIntegration:
    """Integration tests for metrics."""

    def test_all_metrics_registered(self):
        """Test that all expected metrics are registered."""
        from agenteval.metrics import list_metrics

        metrics = list_metrics()

        # Check for expected metrics
        expected = [
            "completion_rate",
            "token_usage",
            "execution_time",
            "api_cost",
            "accuracy",
            "instruction_following",
        ]

        for expected_metric in expected:
            assert expected_metric in metrics, f"Expected metric {expected_metric} not found"

    def test_metrics_can_be_instantiated(self):
        """Test that all metrics can be instantiated."""
        from agenteval.metrics import list_metrics, get_metric

        metrics = list_metrics()

        for metric_name in metrics:
            try:
                metric = get_metric(metric_name)
                assert metric is not None
            except Exception as e:
                pytest.fail(f"Failed to instantiate metric {metric_name}: {e}")
