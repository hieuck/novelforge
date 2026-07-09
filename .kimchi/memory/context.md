# Project Context

Keywords: project, purpose, tech-stack, default-branch, package-manager, build, test, repo-url

## Basics

- **Project name**: novelforge
- **Purpose**: Offline-first AI-powered novel writing studio (Electron + FastAPI).
- **Default branch**: main
- **Repository URL**: https://github.com/hieuck/novelforge.git

## Tech stack

- **Frontend**: Electron + React + TypeScript + Vite + Tailwind CSS + Zustand + react-i18next
- **Backend**: FastAPI + SQLAlchemy + SQLite + Pydantic + Uvicorn
- **Shared**: `@novelforge/shared` workspace package for i18n locales + types
- **Package manager**: npm workspaces
- **Build tool**: Vite (frontend), uvicorn (backend engine)
- **Test frameworks**: pytest (backend), vitest (frontend), Playwright (E2E)
- **Lint/Format**: ruff (Python), eslint + tsc + prettier-ish JSON (frontend)

## Common commands

- Install dependencies: `npm install` (root) and ensure `apps/engine/.venv` exists with Python deps
- Run dev: `npm run dev` (root) or `python scripts/dev.py`
- Run backend tests: `cd apps/engine && .venv/Scripts/python -m pytest -v --ignore=tests/test_agent_websocket.py --ignore=tests/test_ai_ws.py --ignore=tests/test_agent_integration.py`
- Run frontend tests: `cd apps/desktop && npx vitest run`
- Run frontend build: `cd apps/desktop && npm run build`
- Run lint: `cd apps/engine && ruff check apps/engine/ --select=E,F,I,N,W,UP --ignore=E501`
- Run pre-commit: `pre-commit run --all-files`

## Notes

- Engine venv is at `apps/engine/.venv` and uses Python 3.11; CI uses Python 3.12.
- Pre-commit hook enforces ruff format; CI ignores `E501` so pre-commit config must match.
- `@novelforge/shared` must be declared as a dependency of `apps/desktop` and must use `i18next` + `react-i18next` as peer dependencies to avoid duplicate i18next instances.
- Writing statistics (v0.9) added: `WritingSession` model, `GET /api/projects/{id}/writing-stats`, Dashboard widget, daily goal in project settings.
- Rich text editor (v0.10) added: Markdown toolbar in chapter editor, Markdown preview, and Markdown rendering in HTML export.
- Dependency PR #27 (`@vitejs/plugin-react` 4.7.0 → 6.0.3) resolved by migrating to Vite 8 (PR #35).
- Worktrees should be created under `.kimchi/worktrees/<branch>/` (already ignored).
