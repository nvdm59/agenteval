"""YAML benchmark loader."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Union

from agenteval.schemas.benchmark import (
    Benchmark,
    BenchmarkConfig,
    BenchmarkMetadata,
    BenchmarkSuite,
    MetricsConfig,
    ReportingConfig,
    SuccessCriterion,
    Task,
    TaskDefinition,
    TaskSetup,
    ValidationConfig,
)


class BenchmarkLoader:
    """
    Loader for YAML benchmark definitions.

    Supports loading:
    - Individual task files
    - Benchmark suite files (that reference multiple tasks)
    - Inline task definitions
    """

    @staticmethod
    def load_task(file_path: Union[str, Path]) -> Task:
        """
        Load a single task from YAML file.

        Args:
            file_path: Path to task YAML file

        Returns:
            Task object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Task file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            return BenchmarkLoader._parse_task(data)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading task from {file_path}: {e}")

    @staticmethod
    def load_suite(file_path: Union[str, Path]) -> Benchmark:
        """
        Load a benchmark suite from YAML file.

        Args:
            file_path: Path to suite YAML file

        Returns:
            Benchmark object with loaded tasks

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Suite file not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            # Parse suite metadata
            suite = BenchmarkSuite(
                name=data.get("name", file_path.stem),
                description=data.get("description", ""),
                version=data.get("version", "1.0.0"),
                tasks=data.get("tasks", []),
                config=BenchmarkLoader._parse_config(data.get("config", {})),
                reporting=BenchmarkLoader._parse_reporting(data.get("reporting", {})),
                metadata=data.get("metadata"),
            )

            # Load referenced tasks
            base_dir = file_path.parent
            loaded_tasks: List[Task] = []

            for task_ref in suite.tasks:
                if isinstance(task_ref, str):
                    # Simple file reference
                    task_path = base_dir / task_ref
                    task = BenchmarkLoader.load_task(task_path)
                    loaded_tasks.append(task)

                elif isinstance(task_ref, dict):
                    # Dict with file and optional weight
                    task_file = task_ref.get("file")
                    if task_file:
                        task_path = base_dir / task_file
                        task = BenchmarkLoader.load_task(task_path)
                        # Add weight to metadata if present
                        if "weight" in task_ref:
                            task.metadata.tags.append(f"weight:{task_ref['weight']}")
                        loaded_tasks.append(task)

            return Benchmark(suite=suite, loaded_tasks=loaded_tasks)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading suite from {file_path}: {e}")

    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> Task:
        """
        Load a task from a dictionary (for programmatic creation).

        Args:
            data: Task data dictionary

        Returns:
            Task object
        """
        return BenchmarkLoader._parse_task(data)

    @staticmethod
    def _parse_task(data: Dict[str, Any]) -> Task:
        """Parse task data into Task object."""
        # Parse metadata
        metadata_data = data.get("metadata", {})
        metadata = BenchmarkMetadata(**metadata_data)

        # Parse task definition
        task_data = data.get("task", {})

        # Parse setup if present
        setup = None
        if "setup" in task_data:
            setup = TaskSetup(**task_data["setup"])

        # Parse success criteria
        success_criteria = []
        if "success_criteria" in task_data:
            for criterion_data in task_data["success_criteria"]:
                success_criteria.append(SuccessCriterion(**criterion_data))

        # Parse validation
        validation_data = task_data.get("validation", {"method": "rule_based"})
        validation = ValidationConfig(**validation_data)

        # Build task definition
        task_def = TaskDefinition(
            type=task_data.get("type", "general"),
            instructions=task_data.get("instructions", ""),
            setup=setup,
            initial_state=task_data.get("initial_state"),
            tools=task_data.get("tools"),
            success_criteria=success_criteria,
            validation=validation,
            expected_output=task_data.get("expected_output"),
            context=task_data.get("context"),
        )

        # Parse metrics
        metrics_data = data.get("metrics", {})
        metrics = MetricsConfig(**metrics_data)

        return Task(metadata=metadata, task=task_def, metrics=metrics)

    @staticmethod
    def _parse_config(data: Dict[str, Any]) -> BenchmarkConfig:
        """Parse benchmark configuration."""
        return BenchmarkConfig(**data)

    @staticmethod
    def _parse_reporting(data: Dict[str, Any]) -> ReportingConfig:
        """Parse reporting configuration."""
        return ReportingConfig(**data)

    @staticmethod
    def validate_task_file(file_path: Union[str, Path]) -> bool:
        """
        Validate a task YAML file without fully loading it.

        Args:
            file_path: Path to task file

        Returns:
            True if valid, False otherwise
        """
        try:
            BenchmarkLoader.load_task(file_path)
            return True
        except Exception:
            return False

    @staticmethod
    def list_tasks_in_suite(file_path: Union[str, Path]) -> List[str]:
        """
        List task names in a suite file.

        Args:
            file_path: Path to suite file

        Returns:
            List of task IDs
        """
        try:
            benchmark = BenchmarkLoader.load_suite(file_path)
            return [task.task_id for task in benchmark.loaded_tasks]
        except Exception:
            return []


# Convenience functions
def load_task(file_path: Union[str, Path]) -> Task:
    """
    Load a task from YAML file.

    Args:
        file_path: Path to task YAML file

    Returns:
        Task object
    """
    return BenchmarkLoader.load_task(file_path)


def load_suite(file_path: Union[str, Path]) -> Benchmark:
    """
    Load a benchmark suite from YAML file.

    Args:
        file_path: Path to suite YAML file

    Returns:
        Benchmark object
    """
    return BenchmarkLoader.load_suite(file_path)


def load_from_dict(data: Dict[str, Any]) -> Task:
    """
    Load a task from dictionary.

    Args:
        data: Task data dictionary

    Returns:
        Task object
    """
    return BenchmarkLoader.load_from_dict(data)
