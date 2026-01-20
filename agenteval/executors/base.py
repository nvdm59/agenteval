"""Base executor class for task execution."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import json
from pathlib import Path

from agenteval.adapters.base import BaseAdapter
from agenteval.schemas.benchmark import Task
from agenteval.schemas.execution import (
    AgentMessage,
    AgentTrace,
    AgentTurn,
    BenchmarkResult,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    MessageRole,
    TokenUsage,
    ToolCall,
)
from agenteval.config import get_settings


class BaseExecutor(ABC):
    """
    Base class for task executors.

    Executors orchestrate the execution of benchmark tasks using
    adapters and capture detailed execution traces.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize executor.

        Args:
            config: Configuration dictionary with:
                - timeout: Task timeout in seconds
                - max_retries: Maximum retries for failed tasks
                - save_traces: Whether to save traces
                - trace_dir: Directory for saving traces
        """
        self.config = config or {}
        self.settings = get_settings()
        self.traces: List[AgentTrace] = []
        self.results: List[ExecutionResult] = []

    @abstractmethod
    async def execute_task(
        self, task: Task, adapter: BaseAdapter, context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute a single task.

        Args:
            task: Task to execute
            adapter: Adapter to use for execution
            context: Optional execution context

        Returns:
            ExecutionResult with outcome
        """
        pass

    @abstractmethod
    async def execute_benchmark(
        self, tasks: List[Task], adapter: BaseAdapter, **kwargs
    ) -> BenchmarkResult:
        """
        Execute entire benchmark.

        Args:
            tasks: List of tasks to execute
            adapter: Adapter to use
            **kwargs: Additional configuration

        Returns:
            BenchmarkResult with aggregated results
        """
        pass

    def _create_context(self, task: Task, adapter: BaseAdapter) -> ExecutionContext:
        """
        Create execution context for a task.

        Args:
            task: Task to execute
            adapter: Adapter being used

        Returns:
            ExecutionContext
        """
        timeout = self.config.get("timeout", self.settings.task_timeout)
        max_turns = task.task.setup.max_turns if task.task.setup else 10

        return ExecutionContext(
            task_id=task.task_id,
            adapter_name=adapter.adapter_name,
            timeout=timeout,
            max_turns=max_turns,
            config=self.config,
        )

    def _create_initial_messages(self, task: Task) -> List[AgentMessage]:
        """
        Create initial messages for task execution.

        Args:
            task: Task to create messages for

        Returns:
            List of AgentMessage
        """
        messages = []

        # Add system message if present in task
        if task.task.context and "system_message" in task.task.context:
            messages.append(
                AgentMessage(
                    role=MessageRole.SYSTEM, content=task.task.context["system_message"]
                )
            )

        # Add task instructions as user message
        messages.append(AgentMessage(role=MessageRole.USER, content=task.task.instructions))

        return messages

    async def _execute_with_timeout(
        self, task: Task, adapter: BaseAdapter, context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute task with timeout protection.

        Args:
            task: Task to execute
            adapter: Adapter to use
            context: Execution context

        Returns:
            ExecutionResult
        """
        try:
            result = await asyncio.wait_for(
                self._execute_task_internal(task, adapter, context), timeout=context.timeout
            )
            return result
        except asyncio.TimeoutError:
            return self._create_timeout_result(task, adapter, context)

    async def _execute_task_internal(
        self, task: Task, adapter: BaseAdapter, context: ExecutionContext
    ) -> ExecutionResult:
        """
        Internal task execution logic.

        Args:
            task: Task to execute
            adapter: Adapter to use
            context: Execution context

        Returns:
            ExecutionResult
        """
        start_time = datetime.now()

        # Create initial messages
        messages = self._create_initial_messages(task)

        # Initialize trace
        trace = AgentTrace(task_id=task.task_id, adapter=adapter.adapter_name, turns=[])

        # Get tool definitions if specified
        tools = None
        if task.task.tool_definitions:
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.parameters or {},
                }
                for tool in task.task.tool_definitions
            ]
        elif task.task.tools:
            # Simple tool names - create basic definitions
            tools = [{"name": tool, "description": "", "parameters": {}} for tool in task.task.tools]

        try:
            # Execute with adapter
            response = await adapter.execute(
                messages=messages, tools=tools, max_turns=context.max_turns
            )

            # Create turn record
            turn = AgentTurn(
                turn_number=1,
                messages=messages + [AgentMessage(role=MessageRole.ASSISTANT, content=response.content)],
                tool_calls=response.tool_calls,
                token_usage=response.token_usage,
                model=response.model,
            )
            trace.turns.append(turn)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            trace.total_time = execution_time

            # Validate task success
            validation_result = {"output": response.content}
            if response.tool_calls:
                validation_result["tools_called"] = [tc.tool for tc in response.tool_calls]

            success = task.validate_success(validation_result)

            # Create result
            result = ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                success=success,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                output=response.content,
                trace=trace,
                turns_count=len(trace.turns),
                token_usage=adapter.get_token_usage(),
                cost=adapter.get_cost(),
                adapter_name=adapter.adapter_name,
                adapter_metadata=adapter.get_metadata(),
                validation_passed=success,
            )

            # Save trace if configured
            if self.config.get("save_traces", self.settings.save_traces):
                self._save_trace(trace)

            self.traces.append(trace)
            self.results.append(result)

            return result

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error=str(e),
                adapter_name=adapter.adapter_name,
                validation_passed=False,
            )

    def _create_timeout_result(
        self, task: Task, adapter: BaseAdapter, context: ExecutionContext
    ) -> ExecutionResult:
        """Create result for timed out execution."""
        now = datetime.now()
        return ExecutionResult(
            task_id=task.task_id,
            status=ExecutionStatus.TIMEOUT,
            success=False,
            start_time=context.start_time,
            end_time=now,
            execution_time=context.timeout,
            error=f"Task exceeded timeout of {context.timeout} seconds",
            adapter_name=adapter.adapter_name,
            validation_passed=False,
        )

    def _save_trace(self, trace: AgentTrace) -> None:
        """
        Save trace to file.

        Args:
            trace: Trace to save
        """
        try:
            trace_dir = Path(self.config.get("trace_dir", self.settings.trace_dir))
            trace_dir.mkdir(parents=True, exist_ok=True)

            timestamp = trace.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"trace_{trace.task_id}_{timestamp}.json"
            filepath = trace_dir / filename

            # Convert to dict for JSON serialization
            trace_dict = trace.model_dump(mode="json")

            with open(filepath, "w") as f:
                json.dump(trace_dict, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save trace: {e}")

    def get_traces(self) -> List[AgentTrace]:
        """Get all captured traces."""
        return self.traces

    def get_results(self) -> List[ExecutionResult]:
        """Get all execution results."""
        return self.results

    def clear_traces(self) -> None:
        """Clear captured traces and results."""
        self.traces.clear()
        self.results.clear()

    def _aggregate_results(
        self, results: List[ExecutionResult], benchmark_name: str, start_time: datetime, adapter: BaseAdapter
    ) -> BenchmarkResult:
        """
        Aggregate task results into benchmark result.

        Args:
            results: List of task results
            benchmark_name: Name of the benchmark
            start_time: Benchmark start time
            adapter: Adapter used

        Returns:
            BenchmarkResult
        """
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        successful = sum(1 for r in results if r.is_successful)
        failed = len(results) - successful

        # Aggregate token usage
        total_usage = TokenUsage()
        for result in results:
            if result.token_usage:
                total_usage += result.token_usage

        # Aggregate costs
        total_cost = sum(r.cost or 0.0 for r in results)

        # Calculate average execution time
        avg_time = sum(r.execution_time for r in results) / len(results) if results else 0.0

        return BenchmarkResult(
            benchmark_name=benchmark_name,
            start_time=start_time,
            end_time=end_time,
            total_time=total_time,
            task_results=results,
            total_tasks=len(results),
            successful_tasks=successful,
            failed_tasks=failed,
            total_token_usage=total_usage,
            total_cost=total_cost,
            average_execution_time=avg_time,
            adapter_name=adapter.adapter_name,
            config=self.config,
        )
