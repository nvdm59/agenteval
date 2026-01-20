# AgentEval

A comprehensive evaluation framework for LLM-based agents with support for benchmark suites, multiple metrics, and both Python library and CLI interfaces.

## Features

- **Multi-Provider Support**: Evaluate agents across Anthropic (Claude), OpenAI (GPT), Google (Gemini), and custom providers
- **Benchmark Suites**: Pre-built benchmarks for web navigation, API calling, reasoning, tool use, and safety
- **Comprehensive Metrics**: Track task success, cost/efficiency, quality, and safety/alignment
- **Flexible Execution**: Sequential or parallel task execution with trace capture
- **Multiple Output Formats**: Console, JSON, HTML reports with visualizations
- **Extensible Architecture**: Easy to add custom adapters, metrics, and benchmarks
- **Type-Safe**: Built with Pydantic for robust data validation

## Installation

```bash
pip install agenteval
```

### Development Installation

```bash
git clone https://github.com/agenteval/agenteval.git
cd agenteval
pip install -e ".[dev]"
```

## Quick Start

### Python Library

```python
import asyncio
from agenteval import AgentEval, Benchmark
from agenteval.adapters import AnthropicAdapter
from agenteval.metrics import CompletionRateMetric, TokenUsageMetric

async def main():
    # Initialize evaluator
    evaluator = AgentEval(save_traces=True)

    # Load benchmark
    benchmark = Benchmark.from_file("benchmarks/web_navigation/suite.yaml")

    # Configure adapter
    adapter = AnthropicAdapter(
        api_key="your-api-key",
        model="claude-3-5-sonnet-20241022"
    )

    # Run evaluation
    results = await evaluator.run(
        benchmark=benchmark,
        adapter=adapter,
        metrics=[CompletionRateMetric(), TokenUsageMetric()],
        parallel=True
    )

    # Generate report
    results.to_html("report.html")
    print(f"Success Rate: {results.get_metric('completion_rate'):.2%}")
    print(f"Total Tokens: {results.get_metric('token_usage')}")

if __name__ == "__main__":
    asyncio.run(main())
```

### CLI

```bash
# Set up environment
export AGENTEVAL_ANTHROPIC_API_KEY=your-api-key

# Run a benchmark
agenteval run web_navigation \
  --adapter anthropic \
  --parallel \
  --output results.json

# List available benchmarks
agenteval list benchmarks

# Generate HTML report
agenteval report results.json \
  --format html \
  --output report.html
```

## Architecture

AgentEval is built on a modular architecture:

### Core Components

1. **Adapters** - Interface layer for LLM providers (Anthropic, OpenAI, etc.)
2. **Benchmarks** - YAML-based task definitions with validation
3. **Executors** - Orchestrate task execution (sequential/parallel)
4. **Metrics** - Compute evaluation metrics (success, cost, quality, safety)
5. **Reporters** - Generate reports in multiple formats

### Directory Structure

```
agenteval/
├── adapters/          # LLM provider adapters
├── benchmarks/        # Benchmark system
├── executors/         # Execution engine
├── metrics/           # Metrics computation
│   ├── success/       # Task success metrics
│   ├── efficiency/    # Cost/performance metrics
│   ├── quality/       # Quality metrics
│   └── safety/        # Safety/alignment metrics
├── reporters/         # Report generation
├── schemas/           # Pydantic data models
├── config/            # Configuration management
└── cli/               # CLI interface
```

## Benchmark Format

Benchmarks are defined in YAML for human readability:

```yaml
metadata:
  name: "simple_task"
  description: "Test basic agent capabilities"
  tags: ["basic", "tutorial"]
  difficulty: "easy"

task:
  type: "general"
  instructions: |
    Complete the following task:
    1. Analyze the input
    2. Generate a response
    3. Validate the output

  tools:
    - "calculator"
    - "web_search"

  success_criteria:
    - type: "output_contains"
      value: "result"

  validation:
    method: "rule_based"

metrics:
  enabled:
    - "task_success_rate"
    - "execution_time"
    - "token_usage"
```

## Available Metrics

### Success Metrics
- **Completion Rate**: Percentage of successfully completed tasks
- **Goal Achievement**: Whether task objectives were met
- **Error Rate**: Frequency of errors during execution

### Efficiency Metrics
- **Token Usage**: Input/output token counts
- **API Cost**: Estimated costs per provider
- **Execution Time**: Time to task completion
- **Turns to Completion**: Number of agent turns required

### Quality Metrics
- **Accuracy**: Exact match and fuzzy matching
- **Correctness**: Rule-based validation
- **LLM Judge**: LLM-as-judge quality evaluation

### Safety Metrics
- **Instruction Following**: Adherence to instructions
- **Harmful Output**: Detection of harmful content
- **Guardrail Violations**: Policy violation detection

## Creating Custom Components

### Custom Adapter

```python
from agenteval.adapters import BaseAdapter, AdapterRegistry

@AdapterRegistry.register("my_provider")
class MyProviderAdapter(BaseAdapter):
    async def execute(self, messages, tools=None, **kwargs):
        # Implement your provider logic
        pass

    def get_token_usage(self):
        return {"input": 100, "output": 50}

    def get_cost(self):
        return 0.002
```

### Custom Metric

```python
from agenteval.metrics import BaseMetric, MetricRegistry

@MetricRegistry.register("my_metric")
class MyCustomMetric(BaseMetric):
    @property
    def metric_type(self):
        return "quality"

    def compute(self, result):
        # Implement metric computation
        score = self._calculate_score(result)
        return MetricResult(name="my_metric", value=score)
```

### Custom Benchmark

```yaml
# my_benchmark.yaml
metadata:
  name: "custom_task"
  description: "My custom evaluation task"

task:
  type: "custom"
  instructions: "Your task instructions here"

  success_criteria:
    - type: "custom_check"
      validator: "my_validator_function"

metrics:
  enabled:
    - "my_metric"
```

## Configuration

AgentEval uses Pydantic Settings for configuration. Settings can be provided via:

1. Environment variables (prefixed with `AGENTEVAL_`)
2. `.env` file
3. Configuration file
4. Command-line arguments

Example `.env`:

```bash
AGENTEVAL_ANTHROPIC_API_KEY=your-key
AGENTEVAL_LOG_LEVEL=INFO
AGENTEVAL_MAX_CONCURRENCY=5
AGENTEVAL_SAVE_TRACES=true
```

## CLI Commands

```bash
# Run benchmark
agenteval run BENCHMARK --adapter ADAPTER [OPTIONS]

# List resources
agenteval list {benchmarks|metrics|adapters} [--tag TAG]

# Validate benchmark file
agenteval validate BENCHMARK_FILE [--strict]

# Generate report
agenteval report RESULTS_FILE --format {console|json|html|csv}

# Replay trace
agenteval replay TRACE_FILE
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/agenteval/agenteval.git
cd agenteval

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agenteval --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
```

### Code Quality

```bash
# Format code
black agenteval tests

# Lint code
ruff agenteval tests

# Type check
mypy agenteval
```

## Examples

See the `examples/` directory for more usage examples:

- `quickstart.py` - Basic usage
- `custom_benchmark.py` - Creating custom benchmarks
- `custom_metric.py` - Implementing custom metrics
- `custom_adapter.py` - Adding new provider adapters
- `notebooks/` - Jupyter notebook tutorials

## Documentation

Full documentation is available at [https://agenteval.readthedocs.io](https://agenteval.readthedocs.io)

- [Getting Started Guide](https://agenteval.readthedocs.io/quickstart)
- [API Reference](https://agenteval.readthedocs.io/api)
- [Benchmark Authoring](https://agenteval.readthedocs.io/benchmarks)
- [Custom Adapters](https://agenteval.readthedocs.io/adapters)
- [Custom Metrics](https://agenteval.readthedocs.io/metrics)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use AgentEval in your research, please cite:

```bibtex
@software{agenteval2026,
  title = {AgentEval: Evaluation Framework for LLM-based Agents},
  author = {AgentEval Team},
  year = {2026},
  url = {https://github.com/agenteval/agenteval}
}
```

## Acknowledgments

- Built with [Anthropic Claude](https://anthropic.com)
- Inspired by evaluation frameworks in the LLM agent community
- Thanks to all contributors

## Support

- GitHub Issues: [https://github.com/agenteval/agenteval/issues](https://github.com/agenteval/agenteval/issues)
- Documentation: [https://agenteval.readthedocs.io](https://agenteval.readthedocs.io)
- Discord: [Join our community](https://discord.gg/agenteval)
