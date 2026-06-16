# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- AGENTS.md — project context file for AI-assisted development
- CI: release workflow for NSIS installer on version tags
- Storyboard: drag-and-drop reorder for chapters
- Storyboard: video export with progress bar via Job polling
- Characters: portrait preview lightbox
- Chapters: scene illustration preview lightbox
- Gallery: image lightbox preview
- Gallery: ConfirmDialog replacing browser confirm()
- Dashboard: loading skeletons for project list
- Dashboard: word count statistics per project
- Backend: global exception handler with structured logging
- Backend: Pydantic input validation (max_length) on all entity routes
- Backend: database indexes on project_id foreign keys
- Backend: auto-schema migration on startup
- Tests: chapter reorder, word_count, project word_count

### Changed
- Error handling: API client now shows toast notifications on user actions
- Error handling: replaced `catch { /* ignore */ }` with toast on delete/generate/reorder
- Updater: default branch changed from master → main
- Updater: fixed root path calculation, cleaned up gecko references
- Models: added index=True on Chapter.project_id, Summary.project_id, Settings.project_id

### Fixed
- Loading state: Dashboard no longer shows empty state while fetching
- Gallery: delete handler now uses api.delete instead of raw fetch
- Gallery: lazy loading on image tags

## [0.1.0] — Initial Release

### Added
- Core CRUD: projects, chapters, characters, lore, timeline
- AI Agent panel with ReAct loop (18 tools, 20 presets)
- Image generation: mock (SVG), OpenAI (DALL-E), ComfyUI providers
- Gallery page with image browsing and deletion
- Storyboard page with scene images and chapter sequencing
- Video export via FFmpeg slideshow
- Full-text search (FTS5) across all entities
- Settings: Ollama model manager (list/pull/delete)
- Settings: AI provider configuration
- Settings: connection test
- i18n: Vietnamese/English runtime switching
- 4-panel layout: sidebar, content, agent panel, status bar
- Electron desktop app with auto-start engine
- NSIS installer for Windows
- Bootstrap script from git clone
- Self-updater via git pull
- CI: GitHub Actions with frontend+backend tests
- Tests: 105 backend (pytest), 49 frontend (vitest), 46 E2E (Playwright)
