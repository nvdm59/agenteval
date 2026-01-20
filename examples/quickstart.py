"""
Quickstart example for AgentEval.

This example shows how to:
1. Create a simple task
2. Set up an adapter
3. Execute the task
4. View results
"""

import asyncio
import os
from agenteval.adapters import get_adapter
from agenteval.schemas.execution import AgentMessage, MessageRole
from agenteval.schemas.benchmark import (
    Task,
    BenchmarkMetadata,
    TaskDefinition,
    TaskType,
    ValidationConfig,
    ValidationMethod,
    SuccessCriterion,
    SuccessCriterionType,
)


async def main():
    """Run a simple evaluation example."""

    print("🚀 AgentEval Quickstart Example\n")

    # Step 1: Create a simple task
    print("📋 Creating a simple task...")

    task = Task(
        metadata=BenchmarkMetadata(
            name="simple_math",
            description="Test agent's ability to solve a math problem",
            tags=["math", "reasoning"],
            difficulty="easy",
        ),
        task=TaskDefinition(
            type=TaskType.REASONING,
            instructions="What is 15 multiplied by 7? Please provide just the numerical answer.",
            validation=ValidationConfig(
                method=ValidationMethod.EXACT_MATCH,
            ),
            success_criteria=[
                SuccessCriterion(
                    type=SuccessCriterionType.OUTPUT_CONTAINS,
                    value="105",
                    description="Output should contain the correct answer: 105",
                )
            ],
            expected_output={"answer": 105},
        ),
    )

    print(f"✅ Task created: {task.metadata.name}")
    print(f"   Description: {task.metadata.description}")
    print(f"   Instructions: {task.task.instructions}\n")

    # Step 2: Set up adapter
    print("🔧 Setting up Anthropic adapter...")

    api_key = os.getenv("AGENTEVAL_ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: AGENTEVAL_ANTHROPIC_API_KEY environment variable not set")
        print("   Please set it with: export AGENTEVAL_ANTHROPIC_API_KEY=your-key-here")
        return

    adapter = get_adapter(
        "anthropic",
        config={
            "api_key": api_key,
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
        },
    )

    print(f"✅ Adapter configured: {adapter.adapter_name}\n")

    # Step 3: Execute the task
    print("🏃 Executing task...")

    messages = [
        AgentMessage(
            role=MessageRole.USER,
            content=task.task.instructions,
        )
    ]

    try:
        response = await adapter.execute(messages=messages)

        print("✅ Task completed!\n")

        # Step 4: Display results
        print("📊 Results:")
        print(f"   Response: {response.content}")
        print(f"   Model: {response.model}")

        if response.token_usage:
            print(f"   Input Tokens: {response.token_usage.input_tokens}")
            print(f"   Output Tokens: {response.token_usage.output_tokens}")
            print(f"   Total Tokens: {response.token_usage.total_tokens}")

        cost = adapter.get_cost()
        print(f"   Estimated Cost: ${cost:.6f} USD")

        # Validate success
        success = task.validate_success({"output": response.content})
        print(f"\n{'✅' if success else '❌'} Task validation: {'PASSED' if success else 'FAILED'}")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        return

    print("\n✨ Quickstart example completed!")
    print("\nNext steps:")
    print("  - Try creating custom benchmarks")
    print("  - Explore different metrics")
    print("  - Run pre-built benchmark suites")
    print("  - Compare multiple adapters")


if __name__ == "__main__":
    asyncio.run(main())
