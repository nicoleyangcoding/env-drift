# Contributing

Thanks for helping. Small pull requests are easiest to review.

## Development setup

```bash
git clone https://github.com/nicoleyangcoding/env-drift
cd env-drift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## Adding a language

Patterns live in `src/env_drift/scan.py`. Add a regular expression to `LANGUAGES`, map the file extensions in `SUFFIXES`, and add a line to the parametrized test in `tests/test_env_drift.py` showing a real-world read it should find.

## Guidelines

- No runtime dependencies.
- Only ever read variable names, never values.
- Prefer missing a read over inventing one. False alarms make people stop running the check.
