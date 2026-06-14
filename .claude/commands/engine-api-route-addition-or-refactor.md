---
name: engine-api-route-addition-or-refactor
description: Workflow command scaffold for engine-api-route-addition-or-refactor in novelforge.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /engine-api-route-addition-or-refactor

Use this workflow when working on **engine-api-route-addition-or-refactor** in `novelforge`.

## Goal

Adds or refactors backend API endpoints, including models, routes, services, and corresponding tests.

## Common Files

- `apps/engine/routes/*.py`
- `apps/engine/models/*.py`
- `apps/engine/services/*.py`
- `apps/engine/tests/*.py`
- `apps/engine/app.py`
- `apps/engine/http_main.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Edit or add files in apps/engine/routes/*.py for endpoint logic.
- Edit or add files in apps/engine/models/*.py for data models.
- Edit or add files in apps/engine/services/*.py for business logic.
- Update or add tests in apps/engine/tests/*.py.
- Update apps/engine/app.py or apps/engine/http_main.py if route registration changes.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.