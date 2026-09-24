# Knowbao Research Workbench UI Design

Date: 2026-08-04
Project: Know包 personal knowledge-base RAG app
Scope: frontend visual redesign and display bug audit/fixes

## Goal

Turn Know包 from an AI-looking chat wrapper into a quiet, professional personal research workbench.

The product name, existing frontend/backend paths, route structure, API paths, and backend static serving path must remain unchanged. The redesign should work after uploading back to the remote environment.

## Design Direction

Chosen direction: research archive desk.

The interface should feel like a long-term workspace for collecting, retrieving, and citing personal knowledge. It should avoid marketing-style hero blocks, oversized gradients, decorative floating cards, and colorful AI-template surfaces.

Core impression:

- Calm, precise, and work-focused.
- Built for repeated daily use.
- More like an archive and reading desk than a chatbot.
- Distinctive signature: assistant answers have a citation rail beside them.

## Visual System

Palette:

- Workspace background: `#F7F8FA`
- Paper surface: `#FFFFFF`
- Primary text: `#18202A`
- Secondary text: `#66717F`
- Primary action: `#315C72`
- Warning/destructive: `#A64B3C`

Typography:

- Use system fonts only.
- Do not introduce remote fonts.
- Use a system Chinese sans stack for headings and body.
- Use system monospace only for timestamps, file types, metadata, or status codes.

Shape and depth:

- General border radius: `6px` to `8px`.
- Avoid nested cards.
- Page sections should use spacing, dividers, and simple surfaces instead of stacked decorative cards.
- Shadows are reserved for dialogs, mobile drawer overlays, and temporary floating menus.

Motion:

- Keep motion restrained and functional.
- No decorative hover lifts.
- Support reduced motion.

## Layout Model

Desktop:

```text
+----------------------+-----------------------------------------------+
| Archive sidebar      | Top status bar                                |
|                      +-----------------------------------------------+
| - Chat               | Main research workspace                       |
| - Knowledge          |                                               |
| - Settings           | Answer records / document cabinet / settings |
|                      |                                               |
+----------------------+-----------------------------------------------+
```

Mobile:

```text
+--------------------------------------------------+
| Compact top bar + menu                           |
+--------------------------------------------------+
| Main workspace                                   |
|                                                  |
| Chat composer / page actions remain reachable    |
+--------------------------------------------------+
| Drawer sidebar overlays only when opened         |
+--------------------------------------------------+
```

## Page Rules

### Chat

The chat page becomes a retrieval record surface.

- Empty state should be compact and utility-oriented.
- User messages can keep a subtle tinted surface.
- Assistant answers should read like research notes, not large AI chat bubbles.
- Sources should appear in a citation rail when space allows.
- On narrow screens, the citation rail collapses under the answer.
- The composer must not cover the final message.
- Long questions, answers, source titles, URLs, and errors must wrap or truncate safely.
- Loading, empty, error, and retry states should use the shared state style.

### Knowledge

The knowledge page becomes a document cabinet.

- Upload remains available but should not dominate the page.
- Document records should be scannable by file name, type, chunk count, update time, status, and actions.
- Long file names must not break the layout.
- Desktop can use a table-like list.
- Mobile should switch to compact document rows/cards.
- Empty state should be short and action-focused.

### Settings

The settings page becomes a stable preferences surface.

- Remove duplicate/conflicting CSS behavior.
- Desktop layout: setting label/description on the left, control on the right.
- Tablet layout: tighter two-column layout without action buttons wrapping badly.
- Mobile layout: single column with label above control.
- Inputs, selects, toggles, disabled states, and action buttons should share sizing and rhythm.
- Destructive actions use the warning color and must not look like normal primary actions.

### Shell

- Sidebar should feel like an archive directory.
- Current navigation state should use a quiet left rail or shallow selected background.
- Top bar should carry only current page context and necessary status/actions.
- Mobile drawer must layer correctly above the page but not permanently block interaction.

## Responsive Audit

Check these viewport groups:

- `>= 1200px`: fixed sidebar, readable main width.
- `900px - 1199px`: compressed sidebar and stable settings/document layouts.
- `640px - 899px`: drawer sidebar, single-column page flow where needed.
- `< 640px`: no horizontal overflow; tables become row/card layouts; composer remains usable.

## State System

Shared state behavior:

- Empty: brief copy plus direct action.
- Loading: inline or local loading state.
- Error: readable message with retry when available.
- Disabled: visibly inactive without losing legibility.
- Success: restrained confirmation.
- Dangerous: reserved for delete, reset, or clear actions.

## Bug Fix Targets

The implementation should specifically inspect and fix:

- `settings.css` duplicate rules and layout overrides.
- Settings grid and action alignment across breakpoints.
- Chat composer overlap with scrollable message area.
- Long text overflow in answers, source blocks, filenames, status text, and errors.
- Sidebar/topbar stacking problems on mobile.
- Knowledge list/table behavior on mobile.
- Focus, hover, disabled, loading, empty, and error state consistency.
- Build output and backend static serving compatibility.

## Non-Goals

- Do not rename project directories.
- Do not move frontend or backend entry points.
- Do not change API contracts unless a display bug requires a tiny defensive frontend adjustment.
- Do not add a heavy UI framework.
- Do not introduce remote fonts or assets required for the app to render.
- Do not convert the app into a landing page or marketing site.

## Verification

After implementation:

- Run frontend build from the existing `frontend` path.
- Confirm the backend still serves `frontend/dist` through the existing path.
- Check main routes: chat, knowledge, settings.
- Check desktop and mobile layouts.
- Check long content examples for overflow.
- Report any verification that cannot be completed locally.

## Self-Review

This design avoids generic AI-app defaults by removing the warm cream/gradient/card-heavy language and replacing it with an archive desk model. The signature citation rail is specific to a RAG knowledge-base workflow and gives the app an identity tied to source-backed answers.

No contradiction found with the user's path constraint: all changes are intended to stay inside existing frontend/backend structure, with no route or build-output relocation.

Potential ambiguity: the user asked for a full UI bug audit but did not name exact broken screens. This design treats the visible primary routes and responsive states as in scope.
