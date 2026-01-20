"""Unit tests for benchmark loading."""

import pytest
from pathlib import Path

from agenteval.benchmarks import BenchmarkLoader, load_task, load_from_dict
from agenteval.schemas.benchmark import Task, TaskType, DifficultyLevel


@pytest.mark.unit
class TestBenchmarkLoader:
    """Test benchmark loading functionality."""

    def test_load_from_dict(self):
        """Test loading task from dictionary."""
        task_data = {
            "metadata": {
                "name": "test_task",
                "description": "A test task",
                "tags": ["test"],
                "difficulty": "easy",
            },
            "task": {
                "type": "general",
                "instructions": "Test instructions",
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)

        assert isinstance(task, Task)
        assert task.metadata.name == "test_task"
        assert task.task.type == TaskType.GENERAL
        assert task.metadata.difficulty == DifficultyLevel.EASY

    def test_load_task_with_success_criteria(self):
        """Test loading task with success criteria."""
        task_data = {
            "metadata": {
                "name": "test_task",
                "description": "A test task",
            },
            "task": {
                "type": "reasoning",
                "instructions": "Solve this problem",
                "success_criteria": [
                    {"type": "output_contains", "value": "42", "required": True}
                ],
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)

        assert len(task.task.success_criteria) == 1
        assert task.task.success_criteria[0].value == "42"

    def test_load_task_with_tools(self):
        """Test loading task with tools."""
        task_data = {
            "metadata": {
                "name": "test_task",
                "description": "A test task",
            },
            "task": {
                "type": "tool_use",
                "instructions": "Use tools",
                "tools": ["calculator", "web_search"],
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)

        assert task.task.tools == ["calculator", "web_search"]

    def test_validate_success_with_output_contains(self):
        """Test task success validation."""
        task_data = {
            "metadata": {
                "name": "test_task",
                "description": "A test task",
            },
            "task": {
                "type": "reasoning",
                "instructions": "What is 2+2?",
                "success_criteria": [
                    {"type": "output_contains", "value": "4", "required": True}
                ],
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)

        # Test with correct output
        result_success = {"output": "The answer is 4"}
        assert task.validate_success(result_success) is True

        # Test with incorrect output
        result_fail = {"output": "The answer is 5"}
        assert task.validate_success(result_fail) is False

    def test_validate_success_with_tool_called(self):
        """Test validation with tool call criterion."""
        task_data = {
            "metadata": {
                "name": "test_task",
                "description": "A test task",
            },
            "task": {
                "type": "tool_use",
                "instructions": "Use calculator",
                "success_criteria": [
                    {"type": "tool_called", "tool": "calculator", "required": True}
                ],
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)

        # Test with tool called
        result_success = {"output": "Result", "tools_called": ["calculator"]}
        assert task.validate_success(result_success) is True

        # Test without tool called
        result_fail = {"output": "Result", "tools_called": []}
        assert task.validate_success(result_fail) is False


@pytest.mark.unit
class TestTaskProperties:
    """Test Task model properties."""

    def test_task_id_property(self):
        """Test task_id property."""
        task_data = {
            "metadata": {"name": "my_test_task", "description": "Test"},
            "task": {
                "type": "general",
                "instructions": "Test",
                "validation": {"method": "rule_based"},
            },
        }

        task = load_from_dict(task_data)
        assert task.task_id == "my_test_task"


@pytest.mark.integration
class TestLoadRealBenchmark:
    """Test loading real benchmark files."""

    def test_load_reasoning_suite(self):
        """Test loading the reasoning benchmark suite."""
        # This requires the actual benchmark files to exist
        suite_path = Path("benchmarks/reasoning/suite.yaml")

        if suite_path.exists():
            from agenteval.benchmarks import load_suite

            benchmark = load_suite(suite_path)

            assert benchmark.task_count > 0
            assert benchmark.suite.name == "Reasoning Suite"
        else:
            pytest.skip("Benchmark file not found")

    def test_load_simple_math_task(self):
        """Test loading simple math task."""
        task_path = Path("benchmarks/reasoning/simple_math.yaml")

        if task_path.exists():
            task = load_task(task_path)

            assert task.task_id == "simple_math"
            assert task.task.type == TaskType.REASONING
            assert len(task.task.success_criteria) > 0
        else:
            pytest.skip("Task file not found")
