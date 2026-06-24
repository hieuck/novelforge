# NovelForge — AI-Powered Novel Writing Studio

## Stack
- **Frontend:** Electron + React + TypeScript + Vite + Tailwind CSS + Zustand + react-i18next
- **Backend:** FastAPI + SQLAlchemy + SQLite + Pydantic + Uvicorn
- **Shared:** `@novelforge/shared` package for i18n locales + types
- **AI:** Ollama (local), OpenAI, custom engines via ReAct agent loop
- **Image Gen:** Mock (SVG), OpenAI DALL-E, ComfyUI (local SD)
- **Video:** FFmpeg slideshow export
- **Testing:** pytest (backend), vitest (frontend), Playwright (E2E)
- **CI:** GitHub Actions (CI + Release)
- **Packaging:** electron-builder → NSIS installer

## Quick Start
```bash
git clone https://github.com/hieuck/novelforge.git
cd novelforge
npm install
uv sync
npm run dev          # starts engine (9000) + frontend (5173)
```

### Production / Bootstrap
The app bootstraps from installed location:
- Repo: `%LOCALAPPDATA%/novelforge/novelforge-agent/`
- Venv: `%LOCALAPPDATA%/novelforge/venv/`
- Engine starts on port 9000 (or next available)
- Electron loads `dist-electron/index.html` via `loadFile()`

## Architecture

### Directory Layout
```
novelforge/
├── apps/
│   ├── desktop/          # Electron + Vite + React SPA
│   │   ├── src/
│   │   │   ├── components/   # Reusable UI (Sidebar, AgentPanel, ConfirmDialog, etc.)
│   │   │   ├── pages/        # Route pages (Dashboard, Chapters, Characters, etc.)
│   │   │   ├── stores/       # Zustand stores (project, chapter, settings, etc.)
│   │   │   ├── lib/          # API client, utilities
│   │   │   └── types/        # TypeScript interfaces
│   │   ├── tests_e2e/        # Playwright tests
│   │   └── scripts/          # Electron build helpers
│   └── engine/           # FastAPI backend
│       ├── routes/           # API route handlers (projects, chapters, characters, etc.)
│       ├── models/           # SQLAlchemy models (Chapter, Project, Character, etc.)
│       ├── services/         # Business logic (AI, image gen, search)
│       ├── scripts/          # Migration scripts
│       ├── db/               # Database session + base
│       └── tests/            # pytest tests
├── scripts/              # Dev/ops scripts (dev.py, self_update.py)
├── packages/shared/      # Shared i18n locales + types
└── .github/              # CI/CD workflows
```

### API Routes (FastAPI, all under `/api`)
| Router | Prefix | Description |
|--------|--------|-------------|
| health | `/api/health` | Health check + DB status |
| health detail | `/api/health/db` | DB size, table count |
| projects | `/api/projects/` | CRUD projects |
| chapters | `/api/chapters/` | CRUD chapters + reorder + duplicate |
| characters | `/api/characters/` | CRUD characters |
| lore | `/api/lore/` | CRUD lore entries |
| timeline | `/api/timeline/` | CRUD timeline events |
| settings | `/api/settings/` | App settings + Ollama model manager |
| ai | `/api/ai` | AI text actions (continue, rewrite, etc.) |
| agent | `/api/agent` | WebSocket ReAct agent loop |
| generate | `/api/generate` + `/api/projects/.../images` | Image generation + gallery + video export |
| jobs | `/api/jobs` | Background job management + WebSocket status |
| export | `/api/export` | Story export (md, txt, html, zip) |
| search | `/api/search` | FTS5 full-text search |
| search count | `/api/projects/{id}/search/count` | Search result count |
| chapter stats | `/api/chapters/{id}/stats` | Per-chapter word/char/sentence stats |
| word counts | `/api/projects/{id}/word-counts` | Word counts per chapter |
| imports | `/api/import` | Import projects/chapters |
| update | `/api/update` | Self-update check + apply |
| backup | `/api/backup` | DB backup, list, download, restore, cleanup |

### Database Models (SQLAlchemy + SQLite)
- `Project` — novel project with metadata
- `Chapter` — chapters with content, word_count, scene_order, illustration_url
- `Character` — character profiles with portrait_url, gender, personality, goals
- `Lore` — world-building entries with tags, relationships
- `TimelineItem` — timeline events with characters, chapters
- `GeneratedImage` — generated images with entity tracking
- `Job` — background job tracking (video export, agent tasks)
- `Settings` / `AppSettings` — configuration
- `Summary` — cached AI summaries

### Key Data Flows

**AI Agent (ReAct Loop):**
1. User sends message via WebSocket `/api/ws/agent`
2. Server runs Think → Act (tool call) → Observe → Reflect cycle
3. 18 available tools: create/update chapters, characters, lore etc.
4. Streams thinking steps and results back to client

**Image Generation:**
1. Frontend POSTs to `/api/generate/image` with prompt + entity info
2. Backend routes to configured provider (mock/openai/comfyui)
3. Saves to `data/generated/`, creates `GeneratedImage` record
4. Returns URL for frontend to display

**Video Export (Job-based):**
1. POST `/api/projects/{id}/storyboard/export-video` → returns job_id
2. Background task processes FFmpeg slideshow
3. Frontend polls `GET /api/jobs/{job_id}` for progress/status
4. On completion, downloads via `GET /api/jobs/{job_id}/video`

## Code Conventions

### Python
- Line length: 120, double quotes, spaces (4 per indent)
- Use Ruff for linting + formatting
- Type hints required on all public functions
- Session management: manual `SessionLocal()` + try/finally close
- Route handlers: FastAPI `APIRouter` with typed Pydantic models

### TypeScript/React
- Functional components with hooks (no classes)
- Zustand for global state
- react-i18next for translations (`useTranslation()`)
- Tailwind CSS for styling (dark theme, slate/indigo palette)
- API calls via `api.get/post/patch/delete` from `lib/api.ts`
- User-action errors: pass `true` as last arg to api methods for toast

## Testing

### Backend Tests
```bash
cd apps/engine
uv run pytest -v --ignore=tests/test_agent_websocket.py --ignore=tests/test_ai_ws.py --ignore=tests/test_agent_integration.py
```

### Frontend Tests
```bash
cd apps/desktop
npx vitest run
```

### E2E Tests
```bash
cd apps/desktop
npx playwright install chromium
npx playwright test tests_e2e/ --config=tests_e2e/playwright.config.ts
```

## Important Constraints
- `"type": "commonjs"` in root `package.json` (ESM breaks Electron asar)
- Vite `base: './'` for relative asset paths in `loadFile()` context
- Electron main process loads as CommonJS
- All API routes registered under `/api` prefix
- No PyInstaller — runs from cloned checkout via uv venv
- FFmpeg required at system PATH for video export
- Image gen default provider is `mock` (no API key needed)
- Default AI model: `gemma3:4b` (fast, reliable for agent planning)
