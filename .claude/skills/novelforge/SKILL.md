```markdown
# novelforge Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns, coding conventions, and common workflows used in the `novelforge` repository. The project is a cross-platform application with a Python backend (engine) and a React-based Electron desktop frontend. You'll learn how to contribute features, refactor code, and maintain consistency across both backend and frontend, following established conventions and workflows.

## Coding Conventions

### File Naming
- **CamelCase** is used for file names.
  - Example: `UserProfile.tsx`, `TextParser.py`

### Import Style
- **Relative imports** are preferred in both Python and TypeScript/JavaScript.
  - Python example:
    ```python
    from .models import User
    from ..services.text import TextParser
    ```
  - TypeScript example:
    ```typescript
    import UserStore from '../stores/UserStore'
    import { usePanel } from './hooks/usePanel'
    ```

### Export Style
- **Mixed exports**: Both default and named exports are used in the frontend.
  - Example:
    ```typescript
    // Named export
    export function useNovel() { ... }

    // Default export
    export default NovelPanel
    ```

### Commit Patterns
- **Conventional commits** with these prefixes:
  - `feat`: New features
  - `fix`: Bug fixes
  - `refactor`: Code refactoring
  - `chore`: Maintenance tasks
- **Average commit message length:** 54 characters
  - Example: `feat: add chapter pagination to novel panel`

## Workflows

### engine-api-route-addition-or-refactor
**Trigger:** When you want to add, update, or refactor an API endpoint in the engine backend.  
**Command:** `/add-engine-api-route`

1. Edit or add files in `apps/engine/routes/*.py` for endpoint logic.
2. Edit or add files in `apps/engine/models/*.py` for data models.
3. Edit or add files in `apps/engine/services/*.py` for business logic.
4. Update or add tests in `apps/engine/tests/*.py`.
5. Update `apps/engine/app.py` or `apps/engine/http_main.py` if route registration changes.

**Example: Adding a new API endpoint**
```python
# apps/engine/routes/novelRoute.py
from fastapi import APIRouter
from ..models.novelModel import Novel
from ..services.novelService import get_novel

router = APIRouter()

@router.get("/novel/{id}")
def read_novel(id: int):
    return get_novel(id)
```

### desktop-feature-development
**Trigger:** When you want to add a new feature, panel, or page to the desktop app.  
**Command:** `/new-desktop-feature`

1. Add or edit React components in `apps/desktop/src/components/*.tsx`.
2. Add or edit pages in `apps/desktop/src/pages/*.tsx`.
3. Update or add state management in `apps/desktop/src/stores/*.ts`.
4. Add or update hooks in `apps/desktop/src/hooks/*.ts`.
5. Update types in `apps/desktop/src/types/*.ts`.
6. Write or update tests in `apps/desktop/tests/*.ts`.
7. Update entry points or the main app file if needed.

**Example: Adding a new panel**
```tsx
// apps/desktop/src/components/NovelPanel.tsx
import React from 'react'

export default function NovelPanel() {
  return <div>Novel Panel</div>
}
```

### engine-bootstrap-or-build-script-update
**Trigger:** When you want to change how the engine is started, built, or bundled.  
**Command:** `/update-engine-build`

1. Edit or remove scripts in `apps/engine/_bootstrap*.py` or `scripts/build_engine.py`.
2. Update `.gitignore` if new artifacts are generated or old ones are removed.
3. Remove or add files in `apps/engine/build_pyinstaller/` if build artifacts change.

**Example: Updating a build script**
```python
# scripts/build_engine.py
import subprocess

def build():
    subprocess.run(["pyinstaller", "apps/engine/app.py"])

if __name__ == "__main__":
    build()
```

## Testing Patterns

- **Frontend:** Uses `vitest` for testing React components and logic.
  - Test files follow the pattern: `*.test.ts`
  - Example:
    ```typescript
    // apps/desktop/tests/NovelPanel.test.ts
    import { render } from '@testing-library/react'
    import NovelPanel from '../src/components/NovelPanel'

    test('renders NovelPanel', () => {
      const { getByText } = render(<NovelPanel />)
      expect(getByText('Novel Panel')).toBeDefined()
    })
    ```
- **Backend:** Python test files are placed in `apps/engine/tests/*.py`.

## Commands

| Command                | Purpose                                                        |
|------------------------|----------------------------------------------------------------|
| /add-engine-api-route  | Add or refactor an API endpoint in the engine backend          |
| /new-desktop-feature   | Add a new feature, panel, or page to the desktop app           |
| /update-engine-build   | Update engine bootstrap or build scripts and related artifacts  |
```