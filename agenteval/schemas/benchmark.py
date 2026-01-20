"""Pydantic schemas for benchmark definitions."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DifficultyLevel(str, Enum):
    """Task difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class TaskType(str, Enum):
    """Types of evaluation tasks."""

    GENERAL = "general"
    WEB_NAVIGATION = "web_navigation"
    API_CALLING = "api_calling"
    REASONING = "reasoning"
    CODING = "coding"
    TOOL_USE = "tool_use"
    CONVERSATION = "conversation"
    SAFETY = "safety"
    CUSTOM = "custom"


class ValidationMethod(str, Enum):
    """Methods for validating task completion."""

    RULE_BASED = "rule_based"
    LLM_JUDGE = "llm_judge"
    CUSTOM = "custom"
    EXACT_MATCH = "exact_match"
    REGEX = "regex"


class SuccessCriterionType(str, Enum):
    """Types of success criteria."""

    OUTPUT_CONTAINS = "output_contains"
    OUTPUT_MATCHES = "output_matches"
    ELEMENT_PRESENT = "element_present"
    TEXT_CONTAINS = "text_contains"
    TOOL_CALLED = "tool_called"
    STATE_REACHED = "state_reached"
    CUSTOM_CHECK = "custom_check"


class BenchmarkMetadata(BaseModel):
    """Metadata for a benchmark or task."""

    name: str = Field(..., description="Unique name of the benchmark/task")
    description: str = Field(..., description="Human-readable description")
    version: str = Field(default="1.0.0", description="Version number")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Task difficulty level"
    )
    author: Optional[str] = Field(default=None, description="Author of the benchmark")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")


class ToolDefinition(BaseModel):
    """Definition of a tool available to the agent."""

    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(default=None, description="Tool description")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool parameters schema"
    )


class SuccessCriterion(BaseModel):
    """Single success criterion for task validation."""

    type: SuccessCriterionType = Field(..., description="Type of criterion")
    description: Optional[str] = Field(default=None, description="Human-readable description")

    # For output-based criteria
    value: Optional[str] = Field(default=None, description="Expected value or pattern")
    case_sensitive: bool = Field(default=False, description="Whether matching is case-sensitive")

    # For element-based criteria (web tasks)
    selector: Optional[str] = Field(default=None, description="CSS selector or XPath")
    text: Optional[str] = Field(default=None, description="Expected text content")

    # For tool-based criteria
    tool: Optional[str] = Field(default=None, description="Tool name that should be called")
    with_arguments: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected tool arguments"
    )

    # For state-based criteria
    state: Optional[Dict[str, Any]] = Field(default=None, description="Expected state")

    # For custom criteria
    validator: Optional[str] = Field(
        default=None, description="Name of custom validator function"
    )
    required: bool = Field(default=True, description="Whether this criterion is required")


class ValidationConfig(BaseModel):
    """Configuration for task validation."""

    method: ValidationMethod = Field(..., description="Validation method to use")
    rules: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Validation rules for rule-based validation"
    )
    criteria: Optional[str] = Field(
        default=None, description="Criteria for LLM judge validation"
    )
    judge_model: Optional[str] = Field(
        default=None, description="Model to use for LLM judge"
    )
    custom_validator: Optional[str] = Field(
        default=None, description="Custom validator function name"
    )
    strict: bool = Field(
        default=False, description="Whether to use strict validation"
    )


class TaskSetup(BaseModel):
    """Setup configuration for a task."""

    environment: Optional[str] = Field(default=None, description="Environment type")
    url: Optional[str] = Field(default=None, description="Starting URL for web tasks")
    timeout: int = Field(default=300, description="Task timeout in seconds")
    max_turns: int = Field(default=10, description="Maximum agent turns")
    fixtures: Optional[Dict[str, str]] = Field(
        default=None, description="Test fixtures/data"
    )


class TaskDefinition(BaseModel):
    """Definition of a single evaluation task."""

    type: TaskType = Field(..., description="Type of task")
    instructions: str = Field(..., description="Task instructions for the agent")

    # Setup
    setup: Optional[TaskSetup] = Field(default=None, description="Task setup configuration")
    initial_state: Optional[Dict[str, Any]] = Field(
        default=None, description="Initial state for the task"
    )

    # Tools
    tools: Optional[List[str]] = Field(
        default=None, description="List of tool names available to agent"
    )
    tool_definitions: Optional[List[ToolDefinition]] = Field(
        default=None, description="Detailed tool definitions"
    )

    # Success criteria
    success_criteria: List[SuccessCriterion] = Field(
        default_factory=list, description="Criteria for task success"
    )

    # Validation
    validation: ValidationConfig = Field(..., description="Validation configuration")

    # Expected output (for verification)
    expected_output: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected output for comparison"
    )

    # Additional context
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for the task"
    )


class MetricsConfig(BaseModel):
    """Configuration for metrics to compute."""

    enabled: List[str] = Field(
        default_factory=list, description="List of enabled metric names"
    )
    custom_metrics: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Custom metric configurations"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metric configuration"
    )


class Task(BaseModel):
    """A complete task definition including metadata."""

    metadata: BenchmarkMetadata = Field(..., description="Task metadata")
    task: TaskDefinition = Field(..., description="Task definition")
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig, description="Metrics configuration"
    )

    @property
    def task_id(self) -> str:
        """Get unique task identifier."""
        return self.metadata.name

    def validate_success(self, result: Dict[str, Any]) -> bool:
        """
        Validate if task was successful based on success criteria.

        Args:
            result: Task execution result

        Returns:
            True if task was successful, False otherwise
        """
        if not self.task.success_criteria:
            return True

        passed = []
        for criterion in self.task.success_criteria:
            if not criterion.required:
                continue

            # Check criterion based on type
            if criterion.type == SuccessCriterionType.OUTPUT_CONTAINS:
                check = criterion.value in str(result.get("output", ""))
                passed.append(check)

            elif criterion.type == SuccessCriterionType.TOOL_CALLED:
                tools_called = result.get("tools_called", [])
                check = criterion.tool in tools_called
                passed.append(check)

            # Add more criterion type checks as needed

        return all(passed) if passed else False


class BenchmarkConfig(BaseModel):
    """Configuration for benchmark execution."""

    parallel_execution: bool = Field(
        default=False, description="Whether to run tasks in parallel"
    )
    max_concurrency: int = Field(default=5, description="Maximum concurrent tasks")
    max_retries: int = Field(default=0, description="Maximum retries per task")
    timeout_per_task: int = Field(default=600, description="Timeout per task in seconds")
    save_traces: bool = Field(default=True, description="Whether to save execution traces")
    stop_on_failure: bool = Field(
        default=False, description="Whether to stop on first failure"
    )


class ReportingConfig(BaseModel):
    """Configuration for reporting."""

    aggregate_metrics: bool = Field(
        default=True, description="Whether to aggregate metrics"
    )
    generate_html: bool = Field(default=True, description="Whether to generate HTML report")
    save_traces: bool = Field(default=True, description="Whether to save execution traces")
    output_format: str = Field(default="json", description="Default output format")


class BenchmarkSuite(BaseModel):
    """A collection of tasks forming a benchmark suite."""

    name: str = Field(..., description="Benchmark suite name")
    description: str = Field(..., description="Suite description")
    version: str = Field(default="1.0.0", description="Suite version")
    tasks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Task references (file paths and weights)"
    )
    config: BenchmarkConfig = Field(
        default_factory=BenchmarkConfig, description="Execution configuration"
    )
    reporting: ReportingConfig = Field(
        default_factory=ReportingConfig, description="Reporting configuration"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v):
        """Validate task list."""
        if not v:
            raise ValueError("Benchmark suite must contain at least one task")
        return v


class Benchmark(BaseModel):
    """A complete benchmark with loaded tasks."""

    suite: BenchmarkSuite = Field(..., description="Suite configuration")
    loaded_tasks: List[Task] = Field(default_factory=list, description="Loaded task objects")

    @property
    def task_count(self) -> int:
        """Get number of tasks in benchmark."""
        return len(self.loaded_tasks)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        for task in self.loaded_tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """Get all tasks with a specific tag."""
        return [task for task in self.loaded_tasks if tag in task.metadata.tags]

    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[Task]:
        """Get all tasks with a specific difficulty."""
        return [task for task in self.loaded_tasks if task.metadata.difficulty == difficulty]
