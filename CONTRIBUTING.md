# Contributing to Codabench

Thank you for your interest in contributing!

## Development setup

Follow the Quick installation section in the README. Prefer the completed `.env.example` when creating your local `.env`.

## Branch naming

- `feature/<short-description>`
- `fix/<issue-or-description>`
- `docs/<description>`
- `test/<description>`

## Running tests locally

```bash
# Unit / integration
uv run pytest --cov=src --cov-report=term-missing

# Full e2e (requires Docker)
./scripts/run_e2e.sh
```
# Linting
```bash
flake8 src compute_worker
```
Please run tests and lint before opening a pull request. 

# Pull requests 
- Keep PRs focused and reasonably sized.
- Include a clear description of the change and any related issue.
- Ensure CI is green.
