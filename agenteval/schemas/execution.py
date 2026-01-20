"""Pydantic schemas for execution results and traces."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status of task execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Role of a message in agent conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentMessage(BaseModel):
    """A single message in agent conversation."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Name of the speaker")
    tool_call_id: Optional[str] = Field(default=None, description="Tool call ID for tool messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolCall(BaseModel):
    """A tool call made by the agent."""

    id: str = Field(..., description="Unique tool call ID")
    tool: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    result: Optional[Any] = Field(default=None, description="Tool result")
    error: Optional[str] = Field(default=None, description="Error if tool call failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = Field(default=0, description="Input tokens used")
    output_tokens: int = Field(default=0, description="Output tokens used")
    total_tokens: int = Field(default=0, description="Total tokens used")
    cache_read_tokens: Optional[int] = Field(default=None, description="Tokens read from cache")
    cache_write_tokens: Optional[int] = Field(default=None, description="Tokens written to cache")

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add token usage from another instance."""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cache_read_tokens=(self.cache_read_tokens or 0) + (other.cache_read_tokens or 0),
            cache_write_tokens=(self.cache_write_tokens or 0) + (other.cache_write_tokens or 0),
        )


class AgentTurn(BaseModel):
    """A single turn in agent execution."""

    turn_number: int = Field(..., description="Turn number (starts at 1)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Turn timestamp")
    messages: List[AgentMessage] = Field(default_factory=list, description="Messages in this turn")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls made")
    token_usage: Optional[TokenUsage] = Field(default=None, description="Token usage for this turn")
    latency: Optional[float] = Field(default=None, description="Latency in seconds")
    model: Optional[str] = Field(default=None, description="Model used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentTrace(BaseModel):
    """Complete trace of agent execution."""

    task_id: str = Field(..., description="Task identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Start timestamp")
    adapter: str = Field(..., description="Adapter used (e.g., anthropic/claude-3-5-sonnet)")
    turns: List[AgentTurn] = Field(default_factory=list, description="Agent turns")
    final_output: Optional[Any] = Field(default=None, description="Final output")
    total_time: Optional[float] = Field(default=None, description="Total execution time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def get_total_token_usage(self) -> TokenUsage:
        """Get total token usage across all turns."""
        total = TokenUsage()
        for turn in self.turns:
            if turn.token_usage:
                total += turn.token_usage
        return total

    def get_tool_calls(self) -> List[ToolCall]:
        """Get all tool calls across all turns."""
        calls = []
        for turn in self.turns:
            calls.extend(turn.tool_calls)
        return calls


class ExecutionContext(BaseModel):
    """Context for task execution."""

    task_id: str = Field(..., description="Task identifier")
    benchmark_name: Optional[str] = Field(default=None, description="Benchmark name")
    adapter_name: str = Field(..., description="Adapter name")
    start_time: datetime = Field(default_factory=datetime.now, description="Execution start time")
    timeout: int = Field(default=300, description="Timeout in seconds")
    max_turns: int = Field(default=10, description="Maximum turns allowed")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")

    class Config:
        arbitrary_types_allowed = True


class ExecutionResult(BaseModel):
    """Result of task execution."""

    task_id: str = Field(..., description="Task identifier")
    status: ExecutionStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Whether task was successful")

    # Timing
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    execution_time: float = Field(..., description="Execution time in seconds")

    # Output
    output: Optional[Any] = Field(default=None, description="Task output")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Trace
    trace: Optional[AgentTrace] = Field(default=None, description="Execution trace")

    # Metrics
    turns_count: int = Field(default=0, description="Number of turns")
    token_usage: Optional[TokenUsage] = Field(default=None, description="Token usage")
    cost: Optional[float] = Field(default=None, description="Estimated cost in USD")

    # Adapter metadata
    adapter_name: str = Field(..., description="Adapter used")
    adapter_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Adapter-specific metadata"
    )

    # Validation results
    validation_passed: bool = Field(default=False, description="Whether validation passed")
    validation_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed validation results"
    )

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        return self.execution_time

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.COMPLETED and self.success


class BenchmarkResult(BaseModel):
    """Result of benchmark execution."""

    benchmark_name: str = Field(..., description="Benchmark name")
    start_time: datetime = Field(..., description="Benchmark start time")
    end_time: datetime = Field(..., description="Benchmark end time")
    total_time: float = Field(..., description="Total execution time in seconds")

    # Task results
    task_results: List[ExecutionResult] = Field(
        default_factory=list, description="Results for each task"
    )
    total_tasks: int = Field(..., description="Total number of tasks")
    successful_tasks: int = Field(..., description="Number of successful tasks")
    failed_tasks: int = Field(..., description="Number of failed tasks")

    # Aggregate metrics
    total_token_usage: Optional[TokenUsage] = Field(
        default=None, description="Total token usage"
    )
    total_cost: Optional[float] = Field(default=None, description="Total cost in USD")
    average_execution_time: float = Field(
        default=0.0, description="Average task execution time"
    )

    # Configuration
    adapter_name: str = Field(..., description="Adapter used")
    config: Dict[str, Any] = Field(default_factory=dict, description="Benchmark configuration")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    def get_task_result(self, task_id: str) -> Optional[ExecutionResult]:
        """Get result for a specific task."""
        for result in self.task_results:
            if result.task_id == task_id:
                return result
        return None

    def get_failed_tasks(self) -> List[ExecutionResult]:
        """Get all failed task results."""
        return [r for r in self.task_results if not r.is_successful]

    def get_successful_tasks(self) -> List[ExecutionResult]:
        """Get all successful task results."""
        return [r for r in self.task_results if r.is_successful]


class AgentResponse(BaseModel):
    """Response from agent adapter."""

    content: str = Field(..., description="Response content")
    messages: List[AgentMessage] = Field(
        default_factory=list, description="All messages in conversation"
    )
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls made")
    token_usage: Optional[TokenUsage] = Field(default=None, description="Token usage")
    model: Optional[str] = Field(default=None, description="Model used")
    finish_reason: Optional[str] = Field(default=None, description="Reason for finishing")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
