# Knowbao Research Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Know包 into a quiet personal research workbench and fix primary frontend display bugs without changing existing project paths.

**Architecture:** Keep the existing Vue 3 + Vite + Pinia frontend structure. Make the redesign through the current view/component files and CSS modules, with shared visual rules centralized in `tokens.css`, `base.css`, and shell/page styles. Keep backend API and static hosting behavior unchanged; only inspect backend path compatibility.

**Tech Stack:** Vue 3, Vite 6, Pinia 3, plain CSS, FastAPI static serving from `frontend/dist`.

## Global Constraints

- Keep product name: `Know包`.
- Do not rename project directories.
- Do not move frontend or backend entry points.
- Do not change route structure, API paths, or backend static serving path.
- Do not add a heavy UI framework.
- Do not introduce remote fonts or required remote assets.
- Keep build output at `frontend/dist`.
- Current directory is not a git repository; skip commit steps unless a `.git` repository is restored.

---

## File Structure

- Modify: `frontend/src/styles/tokens.css`
  - Own the research-workbench color, spacing, radius, shadow, typography, and state tokens.
- Modify: `frontend/src/styles/base.css`
  - Own global body, buttons, form controls, focus states, text wrapping, and reduced-motion defaults.
- Modify: `frontend/src/styles/shell.css`
  - Own app frame, sidebar, topbar, drawer, navigation, and mobile layering.
- Modify: `frontend/src/styles/chat.css`
  - Own chat transcript, assistant research note layout, source/citation rail behavior, composer spacing, and chat states.
- Modify: `frontend/src/styles/knowledge.css`
  - Own document cabinet, upload tools, document rows, statistics, and mobile document layout.
- Modify: `frontend/src/styles/settings.css`
  - Own settings-only layout. Remove duplicated/conflicting layout rules by replacing the file with a single stable settings system.
- Modify: `frontend/src/styles/responsive.css`
  - Own cross-page viewport overrides only where page-local CSS is not enough.
- Modify: `frontend/src/components/Sidebar.vue`
  - Keep route behavior; adjust class hooks/copy only if needed for archive navigation.
- Modify: `frontend/src/components/TopBar.vue`
  - Keep props/events; adjust class hooks/copy only if needed for compact status display.
- Modify: `frontend/src/components/SourceBlock.vue`
  - Keep source data contract; adjust markup for citation rail and long text safety if current markup cannot support it with CSS alone.
- Modify: `frontend/src/views/ChatView.vue`
  - Keep API calls and streaming behavior; adjust semantic wrappers/classes for research note layout and safe composer spacing.
- Modify: `frontend/src/views/KnowledgeView.vue`
  - Keep upload/delete/stat behavior; adjust wrappers/classes for document cabinet layout and mobile-safe long names.
- Modify: `frontend/src/views/SettingsView.vue`
  - Keep settings API behavior; adjust wrappers/classes for stable label/control rows.
- Inspect only: `backend/app_server.py`
  - Confirm `FRONTEND_DIST = BASE_DIR / "frontend" / "dist"` remains unchanged.

## Task 1: Baseline Build and Route Inventory

**Files:**
- Inspect: `frontend/package.json`
- Inspect: `frontend/src/App.vue`
- Inspect: `frontend/src/views/ChatView.vue`
- Inspect: `frontend/src/views/KnowledgeView.vue`
- Inspect: `frontend/src/views/SettingsView.vue`
- Inspect: `backend/app_server.py`

**Interfaces:**
- Consumes: existing route/view/component structure.
- Produces: list of exact class names and behavior that later tasks must preserve.

- [ ] **Step 1: Read frontend entry and page markup**

Run:

```bash
sed -n '1,260p' frontend/src/App.vue
sed -n '1,320p' frontend/src/views/ChatView.vue
sed -n '1,320p' frontend/src/views/KnowledgeView.vue
sed -n '1,360p' frontend/src/views/SettingsView.vue
```

Expected: identify current wrapper class names, event handlers, and API calls. Do not edit yet.

- [ ] **Step 2: Read shell and source components**

Run:

```bash
sed -n '1,260p' frontend/src/components/Sidebar.vue
sed -n '1,260p' frontend/src/components/TopBar.vue
sed -n '1,260p' frontend/src/components/SourceBlock.vue
```

Expected: identify props/events that must remain unchanged.

- [ ] **Step 3: Read all CSS modules**

Run:

```bash
sed -n '1,260p' frontend/src/styles/tokens.css
sed -n '1,320p' frontend/src/styles/base.css
sed -n '1,360p' frontend/src/styles/shell.css
sed -n '1,420p' frontend/src/styles/chat.css
sed -n '1,460p' frontend/src/styles/knowledge.css
sed -n '1,520p' frontend/src/styles/settings.css
sed -n '1,420p' frontend/src/styles/responsive.css
```

Expected: record duplicated selectors, especially settings selectors that conflict across files.

- [ ] **Step 4: Run baseline build**

Run:

```bash
cd frontend
pnpm build
```

Expected: build either passes or fails for a pre-existing reason. If it fails, capture the exact error before changing code.

## Task 2: Shared Visual Foundation

**Files:**
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/styles/base.css`

**Interfaces:**
- Consumes: existing CSS custom properties used by page styles.
- Produces: stable tokens for workbench colors, borders, text, focus, state, and form controls.

- [ ] **Step 1: Update tokens**

In `frontend/src/styles/tokens.css`, replace warm cream, gradient-heavy, and oversized radius defaults with these token values while preserving existing token names wherever possible:

```css
:root {
  --paper-ground: #f7f8fa;
  --paper-surface: #ffffff;
  --paper-surface-soft: #f2f4f6;
  --ink: #18202a;
  --ink-muted: #66717f;
  --ink-faint: #8a94a3;
  --line: #d9dee5;
  --line-soft: #e8ebef;
  --pine: #315c72;
  --pine-strong: #25495c;
  --amber: #a64b3c;
  --blue: #315c72;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;
  --shadow-soft: none;
  --shadow-lift: 0 16px 40px rgba(24, 32, 42, 0.12);
}
```

Keep any compatibility tokens still referenced by current CSS, but map them to this palette.

- [ ] **Step 2: Normalize global UI primitives**

In `frontend/src/styles/base.css`, ensure:

```css
* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
  color: var(--ink);
  background: var(--paper-ground);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  letter-spacing: 0;
}

button,
input,
textarea,
select {
  font: inherit;
}

button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
a:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--pine) 55%, transparent);
  outline-offset: 2px;
}

.truncate {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.break-anywhere {
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
```

Adapt selectors to the existing file structure instead of duplicating incompatible resets.

- [ ] **Step 3: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 3: Shell, Sidebar, and Top Bar

**Files:**
- Modify: `frontend/src/styles/shell.css`
- Modify: `frontend/src/styles/responsive.css`
- Modify only if needed: `frontend/src/components/Sidebar.vue`
- Modify only if needed: `frontend/src/components/TopBar.vue`

**Interfaces:**
- Consumes: existing navigation route events and page title/status props.
- Produces: archive-directory shell with stable desktop and mobile layering.

- [ ] **Step 1: Remove decorative shell treatment**

In `shell.css`, remove page-wide gradients, heavy shadows, oversized rounded containers, and hover lift effects from the shell, sidebar, and topbar.

Use:

```css
.app-shell {
  min-height: 100vh;
  background: var(--paper-ground);
  color: var(--ink);
}

.sidebar {
  background: var(--paper-surface);
  border-right: 1px solid var(--line);
}

.topbar {
  background: color-mix(in srgb, var(--paper-ground) 92%, white);
  border-bottom: 1px solid var(--line-soft);
}
```

Match actual class names found in Task 1.

- [ ] **Step 2: Make active navigation quiet and readable**

For active sidebar nav classes, use a left rail or shallow background:

```css
.nav-item.is-active {
  color: var(--ink);
  background: #eef3f5;
  box-shadow: inset 3px 0 0 var(--pine);
}
```

Do not use gradient active pills.

- [ ] **Step 3: Fix mobile drawer layering**

In `shell.css` and `responsive.css`, ensure the drawer overlay has a higher z-index than page content and lower z-index than dialogs:

```css
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(24, 32, 42, 0.28);
}

.sidebar {
  z-index: 50;
}

.dialog-backdrop {
  z-index: 80;
}
```

Use actual selectors from current components.

- [ ] **Step 4: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 4: Chat Research Record Layout

**Files:**
- Modify: `frontend/src/views/ChatView.vue`
- Modify: `frontend/src/components/SourceBlock.vue`
- Modify: `frontend/src/styles/chat.css`
- Modify if needed: `frontend/src/styles/markdown.css`
- Modify if needed: `frontend/src/styles/responsive.css`

**Interfaces:**
- Consumes: existing chat store/API streaming behavior.
- Produces: chat messages with safe wrapping, citation rail, and non-overlapping composer.

- [ ] **Step 1: Preserve chat behavior while adding layout hooks**

In `ChatView.vue`, keep existing submit, stream, stop, history, and RAG mode logic unchanged. Add or adjust only class wrappers needed for:

```html
<section class="chat-records">
  <article class="message-record message-record--user">...</article>
  <article class="message-record message-record--assistant">
    <div class="answer-body">...</div>
    <aside class="citation-rail">...</aside>
  </article>
</section>
```

If the current template already has equivalent structures, rename as little as possible.

- [ ] **Step 2: Make SourceBlock citation-safe**

In `SourceBlock.vue`, preserve source prop shape. Ensure file title, snippet, path, score, and metadata containers have classes that can wrap safely:

```html
<div class="source-title break-anywhere" :title="sourceTitle">...</div>
<p class="source-snippet break-anywhere">...</p>
```

Use computed values only if the current component already computes source fields.

- [ ] **Step 3: Implement chat CSS**

In `chat.css`, implement:

```css
.chat-records {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: calc(var(--composer-height, 112px) + 24px);
}

.message-record {
  min-width: 0;
  border-bottom: 1px solid var(--line-soft);
  padding: 18px 0;
}

.message-record--user {
  align-self: flex-end;
  max-width: min(760px, 92%);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: #eef3f5;
  padding: 12px 14px;
}

.message-record--assistant {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 280px);
  gap: 20px;
}

.answer-body,
.citation-rail {
  min-width: 0;
}

.chat-composer {
  position: sticky;
  bottom: 0;
  z-index: 20;
  background: linear-gradient(180deg, rgba(247, 248, 250, 0), var(--paper-ground) 24%);
  padding-top: 18px;
}
```

Adapt selectors to actual current names.

- [ ] **Step 4: Add narrow-screen citation collapse**

In `responsive.css` or `chat.css`:

```css
@media (max-width: 760px) {
  .message-record--assistant {
    grid-template-columns: 1fr;
  }

  .citation-rail {
    border-left: 0;
    border-top: 1px solid var(--line-soft);
    padding-top: 12px;
  }
}
```

- [ ] **Step 5: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 5: Knowledge Document Cabinet

**Files:**
- Modify: `frontend/src/views/KnowledgeView.vue`
- Modify: `frontend/src/styles/knowledge.css`
- Modify if needed: `frontend/src/styles/responsive.css`

**Interfaces:**
- Consumes: existing upload/delete/stat API behavior.
- Produces: stable document cabinet layout and mobile-safe rows.

- [ ] **Step 1: Preserve behavior while adding document row hooks**

In `KnowledgeView.vue`, keep existing upload, delete, refresh, and stats logic unchanged. Add class hooks equivalent to:

```html
<section class="document-cabinet">
  <div class="document-row">
    <div class="document-name truncate" :title="file.name">...</div>
    <div class="document-meta">...</div>
    <div class="document-actions">...</div>
  </div>
</section>
```

Use the actual file object names found in the current component.

- [ ] **Step 2: Implement cabinet CSS**

In `knowledge.css`, create a table-like desktop rhythm:

```css
.document-cabinet {
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper-surface);
  overflow: hidden;
}

.document-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) 120px 120px auto;
  gap: 16px;
  align-items: center;
  min-width: 0;
  border-top: 1px solid var(--line-soft);
  padding: 12px 14px;
}

.document-row:first-child {
  border-top: 0;
}

.document-name,
.document-meta,
.document-actions {
  min-width: 0;
}
```

Adapt to the current fields.

- [ ] **Step 3: Implement mobile document layout**

In `knowledge.css` or `responsive.css`:

```css
@media (max-width: 680px) {
  .document-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .document-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}
```

- [ ] **Step 4: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 6: Settings Layout and CSS Conflict Cleanup

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`
- Replace or heavily simplify: `frontend/src/styles/settings.css`
- Modify if needed: `frontend/src/styles/responsive.css`

**Interfaces:**
- Consumes: existing settings form model and save/reset behavior.
- Produces: one stable settings layout without duplicate selector conflicts.

- [ ] **Step 1: Identify duplicated settings selectors**

Run:

```bash
rg -n "settings-panel|settings-group|setting-field|settings-actions|danger|reset|save" frontend/src/styles frontend/src/views/SettingsView.vue
```

Expected: list selectors to consolidate. Keep selectors used by `SettingsView.vue`, remove contradictory duplicate declarations from CSS.

- [ ] **Step 2: Add stable settings row hooks**

In `SettingsView.vue`, keep current form state, load, save, validation, and reset behavior unchanged. Ensure each setting row has:

```html
<div class="setting-row">
  <div class="setting-copy">
    <label class="setting-label">...</label>
    <p class="setting-hint">...</p>
  </div>
  <div class="setting-control">...</div>
</div>
```

Use existing field names and `v-model` bindings.

- [ ] **Step 3: Replace conflicting settings CSS with one system**

In `settings.css`, consolidate around:

```css
.settings-panel {
  display: grid;
  gap: 18px;
}

.settings-group {
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper-surface);
}

.setting-row {
  display: grid;
  grid-template-columns: minmax(180px, 280px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  padding: 16px;
  border-top: 1px solid var(--line-soft);
}

.setting-row:first-child {
  border-top: 0;
}

.setting-control,
.setting-control input,
.setting-control textarea,
.setting-control select {
  min-width: 0;
  width: 100%;
}

.settings-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}
```

Add:

```css
@media (max-width: 720px) {
  .setting-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .settings-actions {
    justify-content: stretch;
  }

  .settings-actions > * {
    flex: 1 1 160px;
  }
}
```

- [ ] **Step 4: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 7: Cross-Page Responsive and Long-Content Audit

**Files:**
- Modify: `frontend/src/styles/responsive.css`
- Modify as needed: `frontend/src/styles/chat.css`
- Modify as needed: `frontend/src/styles/knowledge.css`
- Modify as needed: `frontend/src/styles/settings.css`
- Modify as needed: `frontend/src/styles/shell.css`

**Interfaces:**
- Consumes: page layouts from Tasks 3-6.
- Produces: no obvious overflow, overlap, or broken stacking across primary breakpoints.

- [ ] **Step 1: Search for risky fixed widths**

Run:

```bash
rg -n "width: [0-9]+px|min-width: [0-9]+px|max-width|100vw|position: fixed|z-index|overflow" frontend/src/styles
```

Expected: identify values that can cause mobile overflow or stacking bugs.

- [ ] **Step 2: Add safe text behavior to risky containers**

For answer text, source snippets, file names, status text, and errors, ensure the relevant selectors include:

```css
min-width: 0;
overflow-wrap: anywhere;
word-break: break-word;
```

Use `white-space: nowrap` only with `overflow: hidden` and `text-overflow: ellipsis`.

- [ ] **Step 3: Confirm breakpoint behavior**

Ensure CSS has explicit behavior for:

```css
@media (max-width: 1199px) { }
@media (max-width: 899px) { }
@media (max-width: 639px) { }
```

The exact selectors can live in page files or `responsive.css`, but there must be no conflicting duplicate definitions that reverse earlier tasks.

- [ ] **Step 4: Verify build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS.

## Task 8: Final Verification and Static Hosting Check

**Files:**
- Inspect: `backend/app_server.py`
- Inspect: `frontend/dist/index.html`
- Inspect generated assets under: `frontend/dist/static/`

**Interfaces:**
- Consumes: completed frontend changes.
- Produces: confidence that the remote upload can run with existing frontend/backend paths.

- [ ] **Step 1: Run final frontend build**

Run:

```bash
cd frontend
pnpm build
```

Expected: PASS and generated output in `frontend/dist`.

- [ ] **Step 2: Confirm backend static path**

Run:

```bash
rg -n "FRONTEND_DIST|StaticFiles|frontend/dist|dist" backend/app_server.py frontend/vite.config.js
```

Expected: backend still points to `BASE_DIR / "frontend" / "dist"` and Vite still emits into `frontend/dist`.

- [ ] **Step 3: Inspect generated index asset references**

Run:

```bash
sed -n '1,120p' frontend/dist/index.html
```

Expected: CSS and JS assets are referenced from the built static path that backend already serves.

- [ ] **Step 4: Optional local runtime smoke check**

Run in one terminal:

```bash
cd frontend
pnpm preview --host 127.0.0.1
```

Expected: Vite preview starts and prints a local URL. Open the URL manually and check chat, knowledge, and settings at desktop and mobile widths.

If preview cannot be kept running in the environment, report that build verification passed and manual browser verification was not completed.

## Self-Review

Spec coverage:

- Visual system is covered by Task 2.
- Shell/sidebar/topbar is covered by Task 3.
- Chat research record and citation rail are covered by Task 4.
- Knowledge document cabinet is covered by Task 5.
- Settings CSS conflict cleanup is covered by Task 6.
- Responsive and long-content bugs are covered by Task 7.
- Build and backend static path safety are covered by Task 8.

Placeholder scan:

- No `TBD`, `TODO`, `implement later`, or unbounded "handle edge cases" steps remain.
- Code examples are concrete CSS/HTML targets but allow selector adaptation to the existing Vue structure discovered in Task 1.

Type/interface consistency:

- No new API types are introduced.
- Vue props/events and backend route contracts are preserved.
- The only new shared CSS utility names are `.truncate` and `.break-anywhere`, defined in Task 2 and consumed by later tasks.
