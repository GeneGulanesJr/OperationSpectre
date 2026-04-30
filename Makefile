.PHONY: help install dev-install format lint typecheck test clean setup-dev

help:
	@echo "Available commands:"
	@echo "  setup-dev     - Install all development dependencies and setup pre-commit"
	@echo "  install       - Install production dependencies"
	@echo "  dev-install   - Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  format        - Format code with ruff"
	@echo "  lint          - Lint code with ruff"
	@echo "  typecheck     - Type-check with pyright"
	@echo "  check-all     - Run all code quality checks (format, lint, typecheck)"
	@echo ""
	@echo "Testing:"
	@echo "  test          - Run tests with pytest"
	@echo ""
	@echo "Development:"
	@echo "  pre-commit    - Run pre-commit hooks on all files"
	@echo "  clean         - Clean up cache files and artifacts"

install:
	uv sync --no-dev

dev-install:
	uv sync

setup-dev: dev-install
	uv run pre-commit install
	@echo "Development environment setup complete!"

format:
	uv run ruff format .
	uv run ruff check . --fix

lint:
	uv run ruff check . --fix

check-all: format lint typecheck
	@echo "All code quality checks passed!"

test:
	uv run pytest -v

typecheck:
	uv run pyright opspectre/

pre-commit:
	uv run pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleanup complete!"
