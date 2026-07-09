# Learned Lessons

Keywords: lesson, learned, mistake, gotcha, tip, best-practice

## CI / pre-commit alignment

- The pre-commit hook must use the same ruff rules as CI. CI ignored `E501`, but pre-commit did not, which blocked commits locally even though CI was the source of truth.
- **Best practice**: keep `.pre-commit-config.yaml` and CI workflow lint steps in sync.

## Worktree path masking

- A worktree adds an extra directory level (`repo/.kimchi/worktrees/branch/...`). Code that uses `path.resolve(__dirname, '..', '..')` can work in a worktree but break in CI or production where the file is directly under `repo/apps/desktop/tests_e2e/`.
- **Best practice**: detect repo root by walking up to a known marker (e.g. `package.json` with `workspaces`) instead of hardcoding `..` levels.

## i18next instance deduplication in workspaces

- `@novelforge/shared` initialized its own `i18next` instance while `apps/desktop` used a different hoisted copy. `useTranslation` from `react-i18next` could not see the initialized resources, so components rendered raw translation keys.
- **Fix**: declare `i18next` and `react-i18next` as peer dependencies of the shared package, and initialize with `initReactI18next`.
- **Best practice**: workspace shared packages that integrate with framework hooks should use peer dependencies for those frameworks.

## Missing workspace dependency declaration

- `apps/desktop` imported from `@novelforge/shared` but did not list it in `package.json` dependencies. It happened to resolve via workspace hoisting, but this is fragile.
- **Best practice**: always declare workspace package imports as dependencies.

## Dependency update PR hygiene

- 12 stale Dependabot PRs had failing CI from old `main`, not from the updates themselves. Rebasing them against the fixed `main` is necessary before merging.
- **Best practice**: keep `main` green so dependency PRs can be validated quickly.

## E2E test fragility

- Text-based E2E assertions break whenever copy or i18n changes. Prefer `data-testid` selectors for structural checks.
- **Best practice**: reserve text assertions for user-visible copy that is part of the spec.

## Migrations for new models/columns

- New SQLAlchemy models and columns are created automatically for fresh installs, but existing production DBs need `scripts/migrate.py` to add tables/columns and indexes.
- **Best practice**: whenever a model change is introduced, update `scripts/migrate.py` with matching `ALTER TABLE` / `CREATE TABLE` / `CREATE INDEX` statements.

## Typed project fields vs. generic settings

- Storing a setting like `daily_goal` in the generic `Settings` key/value table keeps strings, but features that need typed values are cleaner as typed columns on `Project`.
- **Best practice**: use typed project columns for core metadata/behavior and keep the generic settings table for open-ended plugin-like config. Update existing tests when defaults change.

## Markdown as a lightweight rich-text format

- Using Markdown syntax stored as plain text avoids new dependencies, keeps the DB schema unchanged, and preserves plain-text fallbacks for `md`/`txt` exports.
- **Best practice**: when adding rich text, prefer a simple markup language over a full editor library unless complex formatting is required; provide a minimal renderer for preview/export.
