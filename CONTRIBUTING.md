# Contributing to NovelForge

## Development Setup

### Prerequisites
- Node.js 20+
- Python 3.11+
- uv (Python package manager)
- Git

### Quick Start
```bash
git clone https://github.com/hieuck/novelforge.git
cd novelforge
npm install
uv sync
npm run dev
```

This starts both the FastAPI engine (port 9000) and Vite frontend (port 5173).

### Running Individual Servers

**Engine only:** `uv run uvicorn app:app --host 127.0.0.1 --port 9000 --reload`
**Frontend only:** `npm run dev`

## Code Quality

### Python (backend)
- We use **Ruff** for linting and formatting
- Run before committing: `ruff check apps/engine/ --fix && ruff format apps/engine/`
- Line length: 120
- Quote style: double quotes

### TypeScript/React (frontend)
- We use **ESLint** with `@typescript-eslint`
- Run before committing: `npm run lint` (from `apps/desktop/`)
- All new components must pass `tsc --noEmit`

### Pre-commit Hooks
Install with: `pre-commit install`
This auto-fixes whitespace, YAML/JSON formatting, and runs Ruff.

## Testing

### Backend
```bash
cd apps/engine
uv run pytest -v --ignore=tests/test_agent_websocket.py
```

### Frontend
```bash
cd apps/desktop
npm run test
```

### E2E (Playwright)
```bash
cd apps/desktop
npx playwright install chromium
npx playwright test tests_e2e/ --config=tests_e2e/playwright.config.ts
```

## Project Structure
```
novelforge/
├── apps/
│   ├── desktop/          # Electron + React frontend (Vite)
│   └── engine/           # FastAPI backend (Python)
├── scripts/              # Dev & deployment scripts
├── packages/
│   └── shared/           # Shared types and i18n locales
├── tests_e2e/            # Playwright end-to-end tests
└── .github/              # CI/CD workflows
```

## Branch Strategy
- `main` — stable, always deployable
- Create feature branches from `main`
- Squash-merge PRs with conventional commit messages

## Commit Messages
Use conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`

## Release Process
See [RELEASE.md](./RELEASE.md).
