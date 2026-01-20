"""Quick test script to verify your API key works."""

import os
import asyncio
from agenteval.adapters import get_adapter


async def test_anthropic_key():
    """Test Anthropic API key."""
    print("🔍 Testing Anthropic API key...")

    api_key = os.getenv("AGENTEVAL_ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ AGENTEVAL_ANTHROPIC_API_KEY not set")
        print("   Set it with: export AGENTEVAL_ANTHROPIC_API_KEY=your-key")
        return False

    print(f"✅ API key found: {api_key[:20]}...")

    try:
        # Create adapter
        adapter = get_adapter(
            "anthropic",
            config={
                "api_key": api_key,
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 50,
            },
        )

        print("📡 Making test API call...")

        # Simple test
        from agenteval.schemas.execution import AgentMessage, MessageRole

        response = await adapter.execute(
            messages=[AgentMessage(role=MessageRole.USER, content="Say 'Hello!'")]
        )

        print(f"✅ API call successful!")
        print(f"   Response: {response.content}")
        print(f"   Tokens used: {response.token_usage.total_tokens if response.token_usage else 'N/A'}")

        cost = adapter.get_cost()
        print(f"   Cost: ${cost:.6f}")

        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


async def test_openai_key():
    """Test OpenAI API key."""
    print("\n🔍 Testing OpenAI API key...")

    api_key = os.getenv("AGENTEVAL_OPENAI_API_KEY")

    if not api_key:
        print("❌ AGENTEVAL_OPENAI_API_KEY not set")
        print("   Set it with: export AGENTEVAL_OPENAI_API_KEY=your-key")
        return False

    print(f"✅ API key found: {api_key[:20]}...")

    try:
        # Create adapter
        adapter = get_adapter(
            "openai",
            config={
                "api_key": api_key,
                "model": "gpt-4o-mini",  # Cheaper for testing
                "max_tokens": 50,
            },
        )

        print("📡 Making test API call...")

        # Simple test
        from agenteval.schemas.execution import AgentMessage, MessageRole

        response = await adapter.execute(
            messages=[AgentMessage(role=MessageRole.USER, content="Say 'Hello!'")]
        )

        print(f"✅ API call successful!")
        print(f"   Response: {response.content}")
        print(f"   Tokens used: {response.token_usage.total_tokens if response.token_usage else 'N/A'}")

        cost = adapter.get_cost()
        print(f"   Cost: ${cost:.6f}")

        return True

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


async def main():
    """Test all configured API keys."""
    print("=" * 60)
    print("  API Key Test")
    print("=" * 60)

    anthropic_ok = await test_anthropic_key()
    openai_ok = await test_openai_key()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"Anthropic: {'✅ Working' if anthropic_ok else '❌ Not configured or failed'}")
    print(f"OpenAI:    {'✅ Working' if openai_ok else '❌ Not configured or failed'}")
    print("=" * 60)

    if anthropic_ok or openai_ok:
        print("\n🎉 You're ready to use AgentEval!")
    else:
        print("\n⚠️  Configure at least one API key to use AgentEval")


if __name__ == "__main__":
    asyncio.run(main())
