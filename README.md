# NovelForge

AI-powered novel writing studio for offline-first story creation.

[![CI](https://github.com/hieuck/novelforge/actions/workflows/ci.yml/badge.svg)](https://github.com/hieuck/novelforge/actions/workflows/ci.yml)

NovelForge helps writers plan, write, and manage novels with the assistance of local or remote AI models. It keeps your manuscript, characters, lore, and timeline organized in one desktop application.

## Features

- **Project-based workspace** — organize novels into projects with metadata and word counts.
- **Chapter editor** — write and reorder chapters with auto-save and word-count tracking.
- **Character bible** — create character profiles with portraits, personality, goals, and relationships.
- **Lore & world-building** — manage locations, factions, magic systems, and other world details.
- **Timeline** — visualise story events and link them to characters and chapters.
- **AI assistant panel** — get AI suggestions, continuations, and rewrites via a ReAct agent loop.
- **Image generation** — generate chapter illustrations with mock, OpenAI DALL-E, or ComfyUI providers.
- **Export** — export projects and chapters to Markdown, plain text, HTML, or ZIP.
- **Search** — full-text search across chapters, lore, and characters with FTS5.
- **Bilingual UI** — English and Vietnamese interface (vi/en).

## Tech Stack

- **Frontend:** Electron + React + TypeScript + Vite + Tailwind CSS + Zustand + react-i18next
- **Backend:** FastAPI + SQLAlchemy + SQLite + Pydantic + Uvicorn
- **Shared:** `@novelforge/shared` workspace package (i18n locales + types)
- **Testing:** pytest (backend), vitest (frontend), Playwright (E2E)

## Quick Start

```bash
git clone https://github.com/hieuck/novelforge.git
cd novelforge
npm install
cd apps/engine && uv sync
npm run dev          # starts engine (port 9000) + frontend (port 5173)
```

## Development

### Backend

```bash
cd apps/engine
.venv/Scripts/python -m uvicorn app:app --host 127.0.0.1 --port 9000 --reload
```

### Frontend

```bash
cd apps/desktop
npm run dev          # Vite dev server on port 5173
```

### Tests

```bash
# Backend
cd apps/engine
.venv/Scripts/python -m pytest -v --ignore=tests/test_agent_websocket.py --ignore=tests/test_ai_ws.py --ignore=tests/test_agent_integration.py

# Frontend unit tests
cd apps/desktop
npx vitest run

# E2E tests (requires engine running and Playwright browsers)
cd apps/desktop
npx playwright install chromium
npx playwright test tests_e2e/ --config=tests_e2e/playwright.config.ts
```

## Building

```bash
# Desktop production build
cd apps/desktop
npm run build
npm run electron:build
```

The installer is produced in `apps/desktop/release/`.

## Configuration

Open **Settings → AI** to choose your AI provider:

- **Ollama** (local, default model `gemma3:4b`)
- **OpenAI** (requires API key)
- Custom engines via the ReAct agent loop

Image generation defaults to the `mock` provider. Switch to OpenAI or ComfyUI in **Settings → Image Generation**.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## License

MIT
