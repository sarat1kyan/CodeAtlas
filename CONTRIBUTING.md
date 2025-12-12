# Contributing to CodeAtlas

Thank you for your interest in contributing to CodeAtlas! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/CodeAtlas.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `pip install -e ".[dev]"`

## Development Setup

```bash
# Clone the repository
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black codeatlas tests
isort codeatlas tests

# Type checking
mypy codeatlas
```

## Code Style

- **Formatting**: We use [Black](https://github.com/psf/black) with line length 100
- **Import sorting**: We use [isort](https://github.com/PyCQA/isort) with Black profile
- **Type hints**: All code should have type hints (checked with mypy)
- **Docstrings**: Use Google-style docstrings

## Testing

- Write tests for all new features
- Ensure all tests pass: `pytest`
- Aim for >= 85% code coverage
- Add integration tests for CLI commands

## Pull Request Process

1. Update CHANGELOG.md with your changes
2. Ensure all tests pass
3. Update documentation if needed
4. Submit a pull request with a clear description

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add new feature`
- `fix: Fix bug in scanner`
- `docs: Update README`
- `test: Add tests for X`
- `refactor: Refactor Y`

## Questions?

Open an issue or contact the maintainers.

Thank you for contributing! 🎉

