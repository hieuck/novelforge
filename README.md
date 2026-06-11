# NovelForge

Offline-first desktop app for novel writing with integrated AI assistant.
Stack: Electron + React + TypeScript + Vite (desktop) / Python FastAPI (AI engine) / SQLite.

## Getting started

```bash
npm install
npm run setup        # install engine venv + dependencies, install desktop deps
npm run dev          # start desktop + engine together
npm run build        # build desktop + engine
```

## Project structure

See monorepo tree:
- `apps/desktop` Electron shell and frontend.
- `apps/engine` FastAPI backend, services, models, routes.
- `packages` shared types, prompts and reusable logic.
