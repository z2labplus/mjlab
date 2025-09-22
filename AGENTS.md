# Repository Guidelines

This guide helps contributors work effectively across the Python backend, React frontend, and Mahjong analysis modules in this repo.

## Project Structure & Module Organization
- `backend/` — FastAPI service. Entry `backend/app/main.py`; config `backend/app/core/config.py` (.env-supported); scripts `backend/start_server.py`; tests `backend/test_*.py`.
- `frontend/` — React (CRA) + TypeScript + Tailwind. Source in `frontend/src`, static assets in `frontend/public`.
- `MahjongKit/` — Core Mahjong logic and utilities with pytest tests.
- `model/` — Training/inference scripts and sample assets (YOLO, data, images).
- Root Python tools — e.g., `video_analyzer.py`, `yolov8_mahjong_detector.py`, and guides (`README.md`, `REPLAY_GUIDE.md`).

## Build, Test, and Development Commands
- Backend env: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Start API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (or `python start_server.py`)
- Frontend setup: `cd frontend && npm install`
- Run UI: `npm start` (proxied to `http://localhost:8000`)
- Python tests: from repo root `pytest -q backend MahjongKit` (some tests call a running API)
- Frontend tests: `cd frontend && npm test`

## Coding Style & Naming Conventions
- Python: PEP8, 4-space indent, type hints; modules/functions `snake_case`, classes `PascalCase`. Use docstrings and keep imports local to `backend/app/*` where possible.
- TypeScript/React: components `PascalCase`, hooks `useX`, variables `camelCase`. Tailwind classes may be co-located with components.
- No enforced linter config; follow existing patterns and keep diffs minimal.

## Testing Guidelines
- Frameworks: `pytest` (Python), CRA/Jest (frontend).
- Name Python tests `test_*.py` next to code (as in `backend/` and `MahjongKit/`).
- For API tests using `requests`, start the backend first.

## Commit & Pull Request Guidelines
- Commits: short, imperative summaries; English or Chinese acceptable (e.g., "Fix hand analysis edge case").
- PRs: clear description, linked issues, change list, screenshots/GIFs for UI, and note any API or contract changes. Update docs when behavior changes.

## Security & Configuration Tips
- Backend loads settings from `.env` via `backend/app/core/config.py`. Do not commit secrets. Examples: `API_PORT=8000`, `REDIS_HOST=localhost`.

## Agent-Specific Notes
- This file applies repo-wide. More specific per-folder guidance may appear (e.g., `backend/AGENTS.md`) and takes precedence within that directory.

