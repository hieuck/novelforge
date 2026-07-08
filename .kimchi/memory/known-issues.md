# Known Issues

Keywords: bug, issue, workaround, limitation, technical-debt, risk

## ISSUE-001: E2E assertions are brittle to i18n text

- **Status**: workaround
- **Impact**: Playwright E2E tests in `apps/desktop/tests_e2e/` rely on translated strings (e.g. "Dashboard", "NovelForge"). If i18n resources fail to load or the default locale changes, tests break.
- **Workaround**: After fixing `initReactI18next` integration, tests currently pass. Long-term, migrate assertions to `data-testid` attributes.
- **Related**: PR #32, `apps/desktop/tests_e2e/`

## ISSUE-002: AI agent WebSocket tests are excluded from CI

- **Status**: open
- **Impact**: `tests/test_agent_websocket.py`, `tests/test_ai_ws.py`, and `tests/test_agent_integration.py` are ignored in CI. Regressions in the AI agent loop are not caught automatically.
- **Workaround**: Manual testing / future dedicated test harness.
- **Related**: `apps/engine/pytest.ini`, `apps/engine/tests/test_agent_*.py`

## ISSUE-003: README and contributor docs are still template text

- **Status**: open
- **Impact**: `README.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` contain Kimchi template placeholders, not product-specific content.
- **Workaround**: Product context is documented in `.kimchi/memory/context.md` and `ROADMAP.md`.
- **Related**: `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`

## ISSUE-004: Major dependency updates need staged validation

- **Status**: open
- **Impact**: Dependabot has opened major updates (zustand v5, @vitejs/plugin-react v6, react-router-dom v7.18) that could introduce breaking changes.
- **Workaround**: Rebase each PR, wait for CI, and merge only after green checks. Consider separate smoke tests for major bumps.
- **Related**: PRs #27, #29, #22

## ISSUE-005: `@vitejs/plugin-react` v6 requires Vite 6

- **Status**: blocked
- **Impact**: Dependabot PR #27 bumps `@vitejs/plugin-react` to 6.0.3, but the plugin imports `vite/internal`, which is not exported in the current Vite 5.x. Frontend CI fails.
- **Workaround**: Keep Vite 5.x and the existing plugin version until Vite 6 migration is validated.
- **Related**: PR #27, `apps/desktop/vite.config.ts`, `apps/desktop/package.json`
