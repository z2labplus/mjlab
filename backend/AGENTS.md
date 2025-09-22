# Repository Guidelines

This backend is a FastAPI service for Mahjong analysis and replays. Use this guide to navigate the codebase and contribute effectively.

## Project Structure & Module Organization
- `app/` — application code
  - `api/` HTTP routes (e.g., `mahjong.py`, `v1/replay.py`)
  - `services/` domain logic and integrations (Redis, replay, standard import)
  - `models/` Pydantic models for requests/responses and records
  - `algorithms/` Mahjong analyzers and helpers
  - `websocket/` WS routes, connection manager, handlers
  - `core/` settings and app events
  - `main.py` FastAPI app factory and router wiring
- `docs/` — format and protocol docs
- Root scripts — utilities and entrypoints (e.g., `start_debug.py`, `start_server.py`)
- Tests — `test_*.py` in repo root (integration-style scripts)

## Build, Test, and Development Commands
- Setup (Python 3.10+):
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run API locally:
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - Redis required (default `localhost:6379`). Example: `docker run -p 6379:6379 -d redis:7-alpine`
- Quick tests:
  - `pytest -q` (some tests are integration and expect the API running and sample data)
  - Or run scripts directly: `python test_api.py`

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; add type hints and concise docstrings.
- Naming: `snake_case` for modules/functions/vars; `PascalCase` for classes.
- API modules live in `app/api`; routers grouped by feature (`/api/mahjong`, `/api/v1/replay`).
- JSON fields use snake_case and explicit nulls (avoid truthy/falsy pitfalls for IDs like `0`).

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio` (installed via `requirements.txt`).
- Place new tests as `test_*.py`. Prefer fast, deterministic unit tests; mark external/IO-heavy tests and provide skips/fallbacks when Redis/API/sample files are unavailable.
- Common patterns: start the API, then call endpoints (see `test_api.py`).

## Commit & Pull Request Guidelines
- Commits: short, imperative, scoped (Chinese or English). Examples:
  - `api: add replay export endpoint`
  - `手牌解析: 修复碰牌逻辑`
- PRs: include summary, motivation, changes, how to test, linked issues, and any API/DB impacts. Add logs/screenshots for behavior changes.

## Security & Configuration Tips
- Configure via environment (.env supported): `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `API_HOST`, `API_PORT`, `DEBUG`, `ALLOWED_ORIGINS`, `LOG_LEVEL`.
- In production: set explicit `ALLOWED_ORIGINS`, disable `DEBUG`, and require Redis auth.
