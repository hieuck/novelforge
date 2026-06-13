# NovelForge

Cong cu viet truyen offline-first voi AI - Scrivener + Obsidian + AI writing studio.

## Tinh nang
- Project management: metadata, chapters, style guide
- Editor: autosave, word count, chapter status (draft/revised/final)
- AI Writing Agent: 19 actions
- Character Bible + Worldbuilding/Lore + Timeline
- Full-text search (FTS5), Job system (WebSocket)
- Export: MD, TXT, HTML, ZIP | Import: .md, .txt

## Yeu cau
- Node.js >= 18, Python >= 3.11
- Ollama hoac OpenAI/OpenRouter API key

## Cai dat
```bash
git clone <repo-url> && cd novelforge
cd apps/engine && python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd ../.. && cd apps/desktop && npm install && cd ../..
```bash

## Chay dev
```bash
# Cach 1: 1 lenh
python scripts/dev.py

# Cach 2: 2 terminal
# Terminal 1:
cd apps/engine && .venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 9000 --reload
# Terminal 2:
cd apps/desktop && npm run dev
```bash
Mo http://localhost:5173 | API docs: http://localhost:9000/docs

## Electron dev
```bash
cd apps/desktop && npm run electron:dev
```bash

## Tests
```bash
# Backend (120/120 passed, 84% coverage):
cd apps/engine
.venv\Scripts\pip install pytest pytest-asyncio pytest-cov httpx
.venv\Scripts\python -m pytest ../../tests/ -v
.venv\Scripts\python -m pytest ../../tests/ --cov=. --cov-report=term-missing

# Frontend (25/25 passed):
cd apps/desktop && npm test
```bash

## Build Windows .exe
```bash
cd apps/desktop
npm run build && npm run electron:build
# Output: apps/desktop/release/
```bash

## Cau hinh AI (Settings trong app)
| Provider | Base URL |
|----------|----------|
| Ollama | http://localhost:11434 |
| OpenAI-compat | https://api.openai.com/v1 |
| OpenRouter | https://openrouter.ai/api/v1 |
| LM Studio | http://localhost:1234/v1 |

TODO security: API key luu SQLite chua ma hoa. Can dung keyring truoc release public.

## Cap nhat tu dong
```bash
# Windows
npm run update
# hoac
python scripts/self_update.py
```

Script sẽ:
- git fetch origin
- so sánh commit hiện tại với remote
- nếu có thay đổi: git reset --hard HEAD + npm install
- nếu không: thông báo "Already up to date"

## Kien truc
```bash
novelforge/
├── apps/
│   ├── desktop/    # Electron + React + TS + Vite
│   └── engine/     # Python FastAPI + SQLite
├── tests/
│   ├── unit/       # Unit tests
│   ├── integration/ # Integration tests
│   └── e2e/        # E2E tests (auto-skip if server down)
└── scripts/dev.py  # Start both servers
```bash
