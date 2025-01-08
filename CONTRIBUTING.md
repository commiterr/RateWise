# Contributing to RateWise

Thank you for your interest in contributing to RateWise! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/RateWise.git
   cd RateWise
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Branch Naming

- `feat/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions/changes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new caching backend
fix: handle edge case in retry logic
docs: update README examples
test: add coverage for circuit breaker
refactor: simplify backoff calculation
chore: update dependencies
```

### Code Style

- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Follow PEP 8 guidelines
- Add type hints to all functions

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check types
mypy src/
```

### Testing

- Write tests for all new functionality
- Maintain test coverage above 85%
- Use pytest fixtures for common test data

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/ratewise --cov-report=term-missing
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Create a pull request with a clear description

## Reporting Issues

When reporting issues, please include:

- Python version
- RateWise version
- Operating system
- Minimal code example to reproduce
- Expected vs actual behavior
- Full error traceback

## Feature Requests

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Search existing issues for similar requests
3. Provide a clear use case
4. Describe the expected behavior

## Questions?

Feel free to open an issue for questions or discussions.

Thank you for contributing!
