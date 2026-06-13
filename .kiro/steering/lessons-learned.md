---
inclusion: auto
description: Project-specific patterns, preferences, and lessons learned over time (user-editable)
---

# Lessons Learned

This file captures project-specific patterns, coding preferences, common pitfalls, and architectural decisions that emerge during development. It serves as a workaround for continuous learning by allowing you to document patterns manually.

**How to use this file:**
1. The `extract-patterns` hook will suggest patterns after agent sessions
2. Review suggestions and add genuinely useful patterns below
3. Edit this file directly to capture team conventions
4. Keep it focused on project-specific insights, not general best practices

---

### WebSocket streaming: use a ref for buffer, not state
When streaming text word-by-word via WebSocket, accumulate into a `useRef` buffer and call `setState` with the ref's value on each delta. The `onmessage` callback is a closure that captures the ref but not stale state:
```ts
const streamBuf = useRef('')
ws.onmessage = (e) => {
  const msg = JSON.parse(e.data)
  if (msg.delta) { streamBuf.current += msg.delta; setStreamText(streamBuf.current) }
  if (msg.done) { store.addAssistantMessage(msg.full ?? streamBuf.current); streamBuf.current = '' }
}
```

### Zustand: define all mutation methods used by non-React callers
When a WS callback calls `useAiStore.getState().addAssistantMessage()` outside of a React hook, that method must be in the store interface. Calling `set()` via `getState()` is safe in Zustand — it bypasses React but the store updates correctly. Always define `addUserMessage` / `addAssistantMessage` helpers alongside the async `sendMessage` action so both HTTP and WebSocket paths can update the same chat history.

### Example: API Error Handling
```typescript
// Always use our custom ApiError class for consistent error responses
throw new ApiError(404, 'Resource not found', { resourceId });
```

---

## Code Style Preferences

*Document team preferences that go beyond standard linting rules.*

### Example: Import Organization
```typescript
// Group imports: external, internal, types
import { useState } from 'react';
import { Button } from '@/components/ui';
import type { User } from '@/types';
```

---

## Kiro Hooks

### `install.sh` is additive-only — it won't update existing installations
The installer skips any file that already exists in the target (`if [ ! -f ... ]`). Running it against a folder that already has `.kiro/` will not overwrite or update hooks, agents, or steering files. To push updates to an existing project, manually copy the changed files or remove the target files first before re-running the installer.

### README.md mirrors hook configurations — keep them in sync
The hooks table and Example 5 in README.md document the action type (`runCommand` vs `askAgent`) and behavior of each hook. When changing a hook's `then.type` or behavior, update both the hook file and the corresponding README entries to avoid misleading documentation.

### Prefer `askAgent` over `runCommand` for file-event hooks
`runCommand` hooks on `fileEdited` or `fileCreated` events spawn a new terminal session every time they fire, creating friction. Use `askAgent` instead so the agent handles the task inline. Reserve `runCommand` for `userTriggered` hooks where a manual, isolated terminal run is intentional (e.g., `quality-gate`).

---

## Common Pitfalls

*Document mistakes that have been made and how to avoid them.*

### Example: Database Transactions
- Always wrap multiple database operations in a transaction
- Remember to handle rollback on errors
- Don't forget to close connections in finally blocks

---

## Architecture Decisions

*Document key architectural decisions and their rationale.*

### Example: State Management
- **Decision**: Use Zustand for global state, React Context for component trees
- **Rationale**: Zustand provides better performance and simpler API than Redux
- **Trade-offs**: Less ecosystem tooling than Redux, but sufficient for our needs

---

## NovelForge-Specific Patterns

### HashRouter + useParams breaks for components outside Routes
With HashRouter, components outside Routes (like Sidebar) get empty object from useParams -- params only injected into route-rendered components. Use useLocation().hash + regex for layout components:
    const projectId = useLocation().hash.match(/#\/projects\/([^/]+)/)?.[1]
Never use useParams() in global layout components with HashRouter.

### Characters/Lore/AI panel only appear inside a project context
These sections are conditional on projectId in URL (React Router useParams). Navigate to root and no project nav shows. Users must open a project from Dashboard first. Document this in help text.

### Model dropdown: Load button + absolute dropdown + outside-click ref
For provider-dependent model selector: keep plain text input for custom models + Load button calling GET /settings/models?provider=...&base_url=... + absolute-positioned dropdown (z-50, max-h-52) + close on outside click via useRef/mousedown. Reusable for any dynamic option list from external API.

### HTTP Content-Disposition: filenames must be ASCII only
Starlette/FastAPI encodes response headers as latin-1. Vietnamese project names in Content-Disposition filename cause UnicodeEncodeError at runtime. Always use NFKD normalization:
`python
def _safe_filename(name):
    import unicodedata
    n = unicodedata.normalize('NFKD', name or 'export').encode('ascii', errors='ignore').decode('ascii')
    safe = ''.join(c if c.isalnum() or c in ' _-' else '_' for c in n)
    return (safe.strip('_ ').replace(' ', '_') or 'export')[:80]
`ash
Applies to any export/download endpoint with user-provided filenames.

### SQLite column naming: use `meta` not `metadata`
SQLAlchemy maps Python attribute names to column names directly. `metadata` is a reserved name in SQLAlchemy's `DeclarativeBase`. Always use `meta` as the column name in models, and map Pydantic field `metadata` → model attribute `meta` in routes:
```python
# In route create handlers:
row = Lore(..., meta=payload.metadata)

# In _apply helpers for PATCH:
setattr(row, "meta" if k == "metadata" else k, v)

# In _to_dict serializers:
"metadata": row.meta
```

### Sub-collection routes must live in the same router as the parent
FastAPI routes under `/api/projects` match in registration order. Routes like `/{project_id}/chapters` must be added to the **same router** as the project CRUD routes. A separate router mounted at the same prefix causes `/{project_id}` to catch `/chapters` as a project ID. Always define sub-collection routes in `routes/projects.py`.

### Vite proxy — no rewrite needed
The Vite dev server proxy forwards `/api` → `http://127.0.0.1:9000`. Since the engine already serves at `/api/...`, do **not** add a `rewrite` rule — it would strip the prefix and break all routes. The correct config is:
```ts
proxy: { '/api': { target: 'http://127.0.0.1:9000', changeOrigin: true, ws: true } }
```

### React autosave: use refs to avoid stale closures
When using `setTimeout` for autosave, the callback captures stale state. Mirror state into refs and read from refs inside the timeout:
```tsx
const titleRef = useRef(title)
useEffect(() => { titleRef.current = title }, [title])
// Inside setTimeout: read titleRef.current, not title
```

### DB schema migrations: SQLite can only ADD columns, not rename
When a column name changes between dev sessions, the safest fix is to revert the model to match the existing DB column name rather than migrating. Run `sqlite3 PRAGMA table_info(table_name)` to inspect actual schema before debugging ORM errors.

### pytest-asyncio: install + asyncio_mode=auto both required
When testing async functions, tests fail with 'async def not supported' unless BOTH: (1) pytest-asyncio installed, (2) pytest.ini has asyncio_mode = auto. Package alone insufficient.

### Vitest test.alias must duplicate resolve.alias
test.alias in vite.config.ts does NOT inherit from resolve.alias. Must repeat same mapping or get 'Failed to resolve import' errors in tests only.

### E2E: auto-skip pattern when server not running
Use _server_available() with short timeout + pytest.mark.skipif so tests skip (not fail) in CI when server is down. Same file works locally (pass) and CI (skip).

### Autosave timer: always clear on unmount
Every component that schedules a `setTimeout` for autosave must clear it on unmount via a cleanup `useEffect`. Otherwise the timeout fires after the component is gone and attempts to `setState` on an unmounted component, causing React warnings or stale API calls:
```tsx
const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
useEffect(() => () => { if (timer.current) clearTimeout(timer.current) }, [])
```

### Pydantic fields that map to reserved SQLAlchemy column names
The `Project` model has a `summary` field. When a form has two textarea fields conceptually distinct (e.g. "project overview summary" vs "author notes"), map them to the two available text columns (`summary` and `description`) rather than adding a new column. This avoids a SQLite ALTER TABLE migration and keeps the schema stable.

### Bootstrap scripts for bulk file generation
When creating many files at once, write a `_bootstrap.py` in `apps/engine/` that uses `pathlib.Path.write_text()`. This generates 20+ files in one command, avoids per-file hook interruptions, and keeps large content out of the conversation. Delete bootstrap scripts after use.

### FTS5 indexing: hook into CRUD routes directly after db.commit()
Call `index_*()` immediately after `db.commit()` in create/update handlers, and `remove_*()` after delete commits. Use lazy imports inside route functions (`from services.search import index_chapter`) to avoid circular imports at module load time. Never index before commit — the row must exist in the DB first.

### FTS5 per-table try/except prevents silent data loss
A malformed FTS5 expression raises `sqlite3.OperationalError` at query time. If one `except` wraps multiple table queries, a bad expression drops results from all tables. Always use individual try/except per table with a LIKE fallback so partial results are still returned to the user.

### Electron production: API URLs must not rely on Vite proxy
In dev, Vite proxies `/api` → `http://127.0.0.1:9000`. In production (`loadFile`), there is no proxy — all `/api/...` fetches fail silently. Detect `app.isPackaged` and inject `window.__ENGINE_PORT__` via IPC before page load. Then in `lib/api.ts`:
```ts
const BASE = (window as any).__ENGINE_PORT__
  ? `http://127.0.0.1:${(window as any).__ENGINE_PORT__}/api`
  : '/api'  // dev: Vite proxy handles it
```

### Python engine must be bundled with PyInstaller for production
End users cannot install Python. Compile: `pyinstaller run.py --onedir --name engine`. Include `dist/engine/` via electron-builder `extraResources`. Electron main spawns `resources/engine/engine.exe` (Windows) / `resources/engine/engine` (macOS/Linux), not `python run.py`.

### Add health-check gate before rendering React app in production
Engine takes 1–3s to start. Without a gate, all API calls fail silently on app open. Poll `http://127.0.0.1:{port}/api/health` from Electron main before `loadFile`, or show a splash screen in the renderer that waits for first successful health check before mounting the router.

### Electron tsconfig must use CommonJS module, not ESModule
The Electron main process runs in Node.js, so `tsconfig.electron.json` must set `"module": "CommonJS"`. Using `"ESNext"` produces files that fail with `require is not defined`. Keep `tsconfig.electron.json` separate from the Vite/React tsconfig.

### LLMClient interface: always add `chat_messages()` alongside `chat()`
The `chat(system, user)` helper is convenient for single-turn calls, but multi-turn history requires passing a full `messages: list[dict]`. Always implement `chat_messages(messages)` as the primary method and make `chat()` a thin wrapper around it. This lets both HTTP and WebSocket endpoints share the same code path:
```python
async def chat(self, *, system: str, user: str) -> str:
    return await self.chat_messages([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
```
Define `chat_stream(messages)` on the base class with a default fallback (yield full result) so the WS handler can always call it without `hasattr` guards.

### Zustand history snapshot: call `getHistory()` before `addUserMessage()`
When building multi-turn AI context, snapshot the conversation history from the store *before* adding the current user message. If you call `getHistory()` after `addUserMessage()`, the current turn appears in the history and gets sent twice to the backend. The correct pattern:
```ts
const history = getHistory()       // snapshot prior turns
addUserMessage(text)               // now add current turn to UI
ws.send(JSON.stringify({ text, history }))  // send both separately
```

### Insert-to-editor: always trigger autosave after programmatic `setContent`
When an AI panel injects text into the editor via a prop callback (`onInsertText`), the `setContent` call bypasses the normal `onChange` → `scheduleAutosave` path. Always call `scheduleAutosave()` explicitly after `setContent` in the callback, otherwise the chapter shows as saved when it has unsaved AI-generated content:
```tsx
onInsertText={(text) => {
  setContent((prev) => prev ? prev + '\n\n' + text : text)
  scheduleAutosave()
}}
```

### Agent plan quality depends on context summary — include IDs for editable entities
The LLM planner can only reference entities it knows about. When building the context summary for the planning step, include entity IDs (not just names) for chapters and other editable items. Without IDs, the LLM cannot generate valid `update_chapter` or similar tool calls:
```python
ctx_summary += "Chapters: " + ", ".join(
    f'"{c.title}" (id={c.id})' for c in ctx.chapters[:5]
) + "\n"
```
Apply the same pattern for any future tool that operates on existing records (update_character, update_lore, etc.).

### Pass projectId/chapterId as props to AI panels — don't re-derive from router
When `Chapters.tsx` already has `projectId` and `chapterId` from `useParams()`, pass them as props to `AiPanel` and `AgentPanel` rather than having each panel re-derive them independently. Re-deriving causes bugs (e.g. hash regex in AgentPanel) and makes the data flow opaque. The pattern:
```tsx
// In Chapters.tsx — single source of truth
<AgentPanel projectId={projectId} />
<AiPanel projectId={projectId} chapterId={chapterId} ... />
// In panels — prefer prop, fall back to useParams for standalone use
const projectId = propProjectId ?? params.projectId ?? null
```

### Agent memory: read tool results must store full content for downstream steps
When an agent reads data (e.g. `read_chapter`) and stores a summary in memory, downstream steps (e.g. `update_chapter`) that need the actual content must be able to extract it from memory — not re-fetch from DB. Structure memory entries with a consistent format and a findable content marker:
```python
# In _tool_result_summary for read_chapter:
f"[read_chapter] Title: {result.get('title')}, ID: {result.get('id')}, ...\nContent: {preview}"

# In extraction helper:
content_marker = "\nContent: "
idx = entry.find(content_marker)
if idx != -1:
    return entry[idx + len(content_marker):]
```
If memory stores only a preview (truncated), the extraction helper must signal that a re-fetch is needed rather than silently returning an empty string.

### Agent tools: always guard empty-string before regex name resolution
When resolving an entity name to an ID via regex over memory, guard against an empty `name_hint` before calling `re.search`. An empty `re.escape("")` matches everywhere and returns the first ID in memory — a silent wrong-ID bug:
```python
name_hint = (params.get("name") or "").strip()
if name_hint:
    m = re.search(rf"\b{re.escape(name_hint)}\b\s*\(id=([^)]+)\)", entry, re.IGNORECASE)
```
Use `\b` word boundaries and `re.IGNORECASE` for robustness. Apply this pattern for any future tool that resolves names → IDs from memory.

### Custom dropdown: always open upward when input is at bottom of a fixed-height panel
In sidebar panels with fixed height (AiPanel, AgentPanel), the input area is always near the bottom. Use `bottom-full mb-1` positioning so dropdowns open upward and never clip. Native `<select>` opens downward and clips in this layout. Apply to any future selector inside a bottom-anchored input area.

### Grouped + searchable selector: derive groups at module level from the data array
When an options array has a `group` field, derive the grouped structure once at module level rather than inside the component render:
```ts
const ACTION_GROUPS = Array.from(
  AI_ACTIONS.reduce((map, a) => {
    const list = map.get(a.group) ?? []
    list.push(a)
    map.set(a.group, list)
    return map
  }, new Map<string, typeof AI_ACTIONS[number][]>()),
)
```
Same pattern applies to any future grouped selector (lore types, chapter statuses, etc.).

### Backend action prompts: UI metadata belongs in types/index.ts, not the backend dict
`_ACTION_PROMPTS` in `routes/ai.py` only needs `value → prompt` pairs. Display labels, groups, icons, and colors belong exclusively in `types/index.ts`. Never mix UI concerns into the backend data contract — it creates a sync burden and couples UI decisions to the Python layer.

### Collapsible AgentPanel sidebar: dùng `flex h-full overflow-hidden` + toggle state
Khi tích hợp AgentPanel vào trang full-width (Characters, Lore, Timeline), dùng layout 2 cột với toggle button trong header. Pattern nhất quán cho mọi trang:
```tsx
// State
const [showAgent, setShowAgent] = useState(false)

// Layout
<div className="flex h-full overflow-hidden">
  <div className="flex flex-1 flex-col overflow-hidden">
    <header>
      {/* Agent toggle button in header */}
      <button onClick={() => setShowAgent(v => !v)} className={showAgent ? 'active-class' : 'inactive-class'}>
        <Bot /> Agent
      </button>
    </header>
    {/* page content */}
  </div>
  {showAgent && (
    <div className="border-l border-slate-800">
      <AgentPanel projectId={projectId} />
    </div>
  )}
</div>
```
Không dùng `flex-col` cho outer div — nó phá layout khi sidebar xuất hiện. Dùng `flex` (row) thay thế.

### WS streaming: capture streamBuf trước khi clear trong step_done handler
Khi WS gửi `step_done`, `streamBuf.current` vẫn còn dữ liệu từ lần stream trước khi được clear. Capture nó trước khi gọi `setStreamText('')`:
```tsx
const streamedText = streamBuf.current  // capture first
setStreamText('')
streamBuf.current = ''
// Then inject into result if needed:
const finalResult =
  tool === 'generate_text' && !rawResult.text && streamedText
    ? { ...rawResult, text: streamedText }
    : rawResult
```
Nếu clear trước khi capture, text sẽ mất và không hiển thị trong tool output card.

---
- Remove patterns that are no longer relevant
- Update patterns as the project evolves
- Focus on what's unique to this project





### WS streaming in non-panel pages: use mountedRef + wsRef for cleanup
When adding inline WS streaming to a page component (not a dedicated panel), use both a `mountedRef` and a `wsRef` cleanup pattern to avoid setState on unmounted components:
```tsx
const wsRef = useRef<WebSocket | null>(null)
const mountedRef = useRef(true)
useEffect(() => () => {
  mountedRef.current = false
  wsRef.current?.close()
}, [])
// In WS callbacks: if (mountedRef.current) setState(...)
```
Without `mountedRef`, closing the WS on unmount triggers `onclose` → `setState` on an unmounted component. Without `wsRef` cleanup, the WS stays open if the user navigates away mid-stream.

### Injecting search results as AI context: strip HTML tags + entities + cap length
When passing FTS5 search excerpts as AI context, strip both HTML tags and entities, then cap excerpt length to avoid token bloat:
```ts
const cleanExcerpt = excerpt
  .replace(/<[^>]+>/g, '')        // remove HTML tags (<b>, etc.)
  .replace(/&[a-z]+;/g, ' ')     // remove HTML entities (&amp;, etc.)
  .slice(0, 150)                  // cap per-result to control token usage
```
FTS5 snippets contain `<b>` highlight tags and potentially `&amp;` etc. Raw injection makes AI context noisy without improving output quality. Apply to any feature that passes DB-fetched text into LLM prompts.

### Dead code in services/: check imports before deleting
`services/ai_service.py` existed as a static prompt dict that duplicated `routes/ai.py` `_ACTION_PROMPTS`. Always run a codebase-wide grep for `import` before deleting any service file — if no matches, it's safe to delete. Dead service files accumulate silently in Python projects since there's no compile-time unused-import error.
