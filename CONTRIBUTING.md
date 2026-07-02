# Contributing

Thanks for your interest in hermes-help!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Install dev dependencies: `uv sync --group dev`
4. Make your changes
5. Run tests: `uv run python -m pytest tests/ -v`
6. Run lint: `uv run ruff check src/`
7. Commit with conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
8. Open a pull request

## Development Setup

```bash
git clone <your-fork>
cd hermes-help
uv sync --group dev
uv run hermes-help schema  # Verify it works
```

## Code Style

- Python 3.12+ with strict type hints
- Ruff linting + formatting (configured in pyproject.toml)
- TDD for new features (tests before code)
- Keep files focused (<300 lines per module)
- Use `__all__` to define public interfaces

## Pull Request Process

1. Ensure all tests pass
2. Add tests for new functionality
3. Update docs if changing behaviour
4. One commit per logical change
