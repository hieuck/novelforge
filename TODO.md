# NovelForge Backlog

## In Progress / Continuous Mode

- [x] Process open dependency-update PRs (#20-#31)
  - Merged #20, #21, #22, #23, #24, #25, #26, #28, #29, #30, #31 on 2026-07-08.
  - #27 closed as superseded by PR #35 (Vite ^8.0.0 + @vitejs/plugin-react ^6.0.3 migration).

## Product Gaps (Roadmap)

- [x] v0.9 Writing statistics (merged via PR #34)
  - Track daily word-count progress.
  - Add per-project daily goals.
  - Surface streaks / history in Dashboard.
- [ ] v0.10 Rich text chapter editor
  - Bold, italic, headings in chapter content.
  - Preserve plain-text fallback for export.
- [ ] v0.11 Multi-format export
  - EPUB export.
  - PDF export.
- [ ] v0.12 Cloud sync (optional, self-hosted)
  - Design sync backend / protocol.

## Polish / Docs

- [x] Replace Kimchi template README with NovelForge product README.
- [ ] Add product screenshot / demo GIF to README.
- [ ] Audit and refresh CONTRIBUTING.md / CODE_OF_CONDUCT.md for the product (currently template text).

## Technical Debt

- [ ] Migrate E2E text assertions to `data-testid` to reduce i18n fragility.
- [ ] Add backend tests for AI agent WebSocket paths (currently ignored in CI).
- [ ] Review and lock major dependency updates in a staged rollout.
