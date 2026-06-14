# NovelForge

Offline-first AI writing studio — một trình soạn thảo tiểu thuyết với AI Agent hỗ trợ.

## Kiến trúc

```
novelforge/
├── apps/
│   ├── desktop/    # Electron + React + Vite (giao diện người dùng)
│   └── engine/     # Python FastAPI (API backend + AI Agent)
└── packages/
    └── shared/     # @novelforge/shared (i18n config, types, locales chung)
```

## Tính năng

- **Project management**: metadata, chapters, style guide, nhân vật, lore, timeline
- **Editor**: autosave (1.5s), word count, chapter status (draft/revised/final), Ctrl+S
- **AI Writing Agent**: 18 tools, plan→execute→adapt loop, preset tasks
- **Character Bible + Worldbuilding/Lore + Timeline**
- **Full-text search** (SQLite FTS5), **Background job system**
- **Export**: MD, TXT, HTML, ZIP | **Import**: .md, .txt
- **i18n**: Tiếng Việt / English (chuyển đổi trong Settings → About)
- **Engine crash recovery**: tự động restart (tối đa 5 lần)
- **Cross-platform**: Windows (NSIS), macOS (DMG), Linux (AppImage)

## Yêu cầu

- Node.js >= 20, Python >= 3.11
- Ollama (mặc định) hoặc OpenAI/OpenRouter API key (cấu hình trong Settings)

## Cài đặt & Chạy dev

```bash
# Clone && cài dependencies
git clone https://github.com/hieuck/novelforge && cd novelforge
npm install                          # root workspace

# Backend (Python)
cd apps/engine && python -m venv .venv
.venv\Scripts\pip install -r requirements.txt && cd ../..

# Frontend (có sẵn từ workspace ở trên)

# Chạy dev (1 lệnh)
python scripts/dev.py

# Hoặc 2 terminal riêng:
# Terminal 1: cd apps/engine && .venv\Scripts\uvicorn app:app --reload --port 9000
# Terminal 2: cd apps/desktop && npm run dev
```

## Build desktop installer

```bash
cd apps/desktop
npm run electron:build    # tạo NSIS installer trong release/
```

## Testing

```bash
# Frontend unit tests
cd apps/desktop && npx vitest run     # 44 tests

# Backend integration tests
cd apps/engine && pytest -v            # 10 tests

# E2E API tests (cần engine đang chạy)
cd apps/desktop && npx vitest run tests_e2e/
```

CI tự động chạy trên GitHub Actions cho mọi push vào `main`.# Terminal 1:
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
