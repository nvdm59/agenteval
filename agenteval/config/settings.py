"""Configuration settings for AgentEval."""

from pathlib import Path
from typing import Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentEvalSettings(BaseSettings):
    """
    Global settings for AgentEval.

    Settings can be configured via:
    1. Environment variables (prefixed with AGENTEVAL_)
    2. .env file
    3. Direct instantiation

    Example:
        # Via environment variable
        export AGENTEVAL_LOG_LEVEL=DEBUG

        # Via .env file
        AGENTEVAL_LOG_LEVEL=DEBUG

        # Via code
        settings = AgentEvalSettings(log_level="DEBUG")
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTEVAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    cache_dir: str = Field(
        default=".agenteval_cache",
        description="Directory for caching results",
    )
    trace_dir: str = Field(
        default=".agenteval_traces",
        description="Directory for saving execution traces",
    )

    # Execution settings
    default_executor: str = Field(
        default="sequential",
        description="Default executor type (sequential, parallel)",
    )
    max_concurrency: int = Field(
        default=5,
        description="Maximum number of concurrent tasks for parallel execution",
    )
    task_timeout: int = Field(
        default=300,
        description="Default timeout for tasks in seconds",
    )
    max_retries: int = Field(
        default=0,
        description="Maximum number of retries for failed tasks",
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models",
    )
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key for Gemini",
    )

    # Model settings
    default_model: Optional[str] = Field(
        default=None,
        description="Default model to use if not specified",
    )

    # Metrics settings
    enable_llm_judge: bool = Field(
        default=False,
        description="Whether to enable LLM-as-judge metrics",
    )
    judge_model: str = Field(
        default="gpt-4",
        description="Model to use for LLM judge",
    )
    enable_all_metrics: bool = Field(
        default=True,
        description="Whether to enable all available metrics by default",
    )

    # Reporting settings
    default_format: str = Field(
        default="console",
        description="Default output format (console, json, html, csv)",
    )
    save_traces: bool = Field(
        default=True,
        description="Whether to save execution traces by default",
    )
    save_results: bool = Field(
        default=True,
        description="Whether to save results to file by default",
    )

    # Cost tracking
    track_costs: bool = Field(
        default=True,
        description="Whether to track and calculate costs",
    )
    cost_limit_per_task: Optional[float] = Field(
        default=None,
        description="Maximum cost per task in USD (None for no limit)",
    )
    cost_limit_per_benchmark: Optional[float] = Field(
        default=None,
        description="Maximum cost per benchmark in USD (None for no limit)",
    )

    # Caching
    enable_cache: bool = Field(
        default=True,
        description="Whether to enable caching of LLM responses",
    )
    cache_ttl: int = Field(
        default=86400,  # 24 hours
        description="Cache time-to-live in seconds",
    )

    # Advanced settings
    stop_on_failure: bool = Field(
        default=False,
        description="Whether to stop benchmark on first failure",
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose output",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    def get_cache_path(self) -> Path:
        """Get the cache directory path."""
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_trace_path(self) -> Path:
        """Get the trace directory path."""
        path = Path(self.trace_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: Provider name (anthropic, openai, google)

        Returns:
            API key if available, None otherwise
        """
        provider = provider.lower()
        if provider in ["anthropic", "claude"]:
            return self.anthropic_api_key
        elif provider in ["openai", "gpt"]:
            return self.openai_api_key
        elif provider in ["google", "gemini"]:
            return self.google_api_key
        return None

    def has_api_key(self, provider: str) -> bool:
        """Check if API key is configured for provider."""
        return self.get_api_key(provider) is not None

    def to_dict(self) -> Dict:
        """Convert settings to dictionary (excluding sensitive data)."""
        data = self.model_dump()
        # Mask API keys
        if data.get("anthropic_api_key"):
            data["anthropic_api_key"] = "***"
        if data.get("openai_api_key"):
            data["openai_api_key"] = "***"
        if data.get("google_api_key"):
            data["google_api_key"] = "***"
        return data


# Global settings instance
_settings: Optional[AgentEvalSettings] = None


def get_settings() -> AgentEvalSettings:
    """
    Get global settings instance.

    Returns:
        AgentEvalSettings instance
    """
    global _settings
    if _settings is None:
        _settings = AgentEvalSettings()
    return _settings


def set_settings(settings: AgentEvalSettings) -> None:
    """
    Set global settings instance.

    Args:
        settings: AgentEvalSettings instance
    """
    global _settings
    _settings = settings


def reset_settings() -> None:
    """Reset settings to default."""
    global _settings
    _settings = None
