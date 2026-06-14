---
name: desktop-feature-development
description: Workflow command scaffold for desktop-feature-development in novelforge.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /desktop-feature-development

Use this workflow when working on **desktop-feature-development** in `novelforge`.

## Goal

Implements new features or panels in the Electron desktop app, including React components, stores, hooks, and tests.

## Common Files

- `apps/desktop/src/components/*.tsx`
- `apps/desktop/src/pages/*.tsx`
- `apps/desktop/src/stores/*.ts`
- `apps/desktop/src/hooks/*.ts`
- `apps/desktop/src/types/*.ts`
- `apps/desktop/tests/*.ts`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Add or edit React components in apps/desktop/src/components/*.tsx.
- Add or edit pages in apps/desktop/src/pages/*.tsx.
- Update or add state management in apps/desktop/src/stores/*.ts.
- Add or update hooks in apps/desktop/src/hooks/*.ts.
- Update types in apps/desktop/src/types/*.ts.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.