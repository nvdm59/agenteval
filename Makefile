.PHONY: help install install-dev test test-unit test-integration coverage lint format typecheck clean docs

help:
	@echo "AgentEval Development Commands"
	@echo "=============================="
	@echo "install          - Install package"
	@echo "install-dev      - Install package with dev dependencies"
	@echo "test             - Run all tests"
	@echo "test-unit        - Run unit tests only"
	@echo "test-integration - Run integration tests only"
	@echo "coverage         - Run tests with coverage report"
	@echo "lint             - Run linters (ruff)"
	@echo "format           - Format code with black"
	@echo "typecheck        - Run type checking with mypy"
	@echo "clean            - Remove build artifacts and cache"
	@echo "docs             - Build documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -v

test-unit:
	pytest -v -m unit

test-integration:
	pytest -v -m integration

coverage:
	pytest --cov=agenteval --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	ruff agenteval tests examples
	@echo "✅ Linting passed!"

format:
	black agenteval tests examples
	@echo "✅ Code formatted!"

typecheck:
	mypy agenteval
	@echo "✅ Type checking passed!"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned!"

docs:
	@echo "Documentation generation not yet implemented"

all: format lint typecheck test
	@echo "✅ All checks passed!"
