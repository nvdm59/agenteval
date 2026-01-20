## Contributing to AgentEval

Thank you for your interest in contributing to AgentEval! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/your-username/agenteval.git
cd agenteval
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

4. **Install pre-commit hooks**

```bash
pre-commit install
```

## Development Workflow

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
black agenteval tests examples

# Lint code
ruff agenteval tests examples

# Type check
mypy agenteval
```

### Running the Example

```bash
# Set your API key
export AGENTEVAL_ANTHROPIC_API_KEY=your-key-here

# Run quickstart
python examples/quickstart.py
```

## Adding New Components

### Adding a New Adapter

1. Create a new file in `agenteval/adapters/`
2. Inherit from `BaseAdapter`
3. Implement all abstract methods
4. Register with `@AdapterRegistry.register()`

Example:

```python
from agenteval.adapters import BaseAdapter, AdapterRegistry

@AdapterRegistry.register("my_provider")
class MyProviderAdapter(BaseAdapter):
    async def execute(self, messages, tools=None, **kwargs):
        # Implementation
        pass

    # Implement other required methods...
```

### Adding a New Metric

1. Create a file in the appropriate `agenteval/metrics/` subdirectory
2. Inherit from `BaseMetric`
3. Implement `compute()` method
4. Register with decorator

### Adding a New Benchmark

1. Create a YAML file in `benchmarks/`
2. Follow the schema defined in documentation
3. Add tests to verify it loads correctly

## Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write clear, concise commit messages
   - Add tests for new features
   - Update documentation as needed

3. **Ensure all checks pass**

```bash
make test
make lint
```

4. **Submit pull request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI passes

## Code Style

- Follow PEP 8 guidelines
- Use Black for formatting (line length: 100)
- Use type hints for function signatures
- Write docstrings for all public methods

## Testing Guidelines

- Write unit tests for all new functionality
- Ensure test coverage stays above 80%
- Use mocks for external API calls in unit tests
- Write integration tests for end-to-end workflows

## Documentation

- Update README.md for user-facing changes
- Add docstrings for all public APIs
- Include examples for new features
- Update the changelog

## Questions?

Open an issue or reach out on Discord.

Thank you for contributing!
