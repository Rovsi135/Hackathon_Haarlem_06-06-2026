Maverx AI Training Builder — Deterministic Frontend Design Spec
=============================================================

Objective
---------
Provide a single, complete, language-agnostic frontend design specification that any capable LLM or frontend engineer can follow to reproduce the exact same UI and UX across implementations and languages.

This document defines:
- design tokens (colors, typography, spacing, radii, shadows)
- exact layout measurements and responsive rules
- accessible DOM structure and ARIA roles
- strict component contracts (props, behavior, events)
- localization keys and examples (so copy can be swapped without layout shifts)
- API stubs and data shapes used by the UI
- visual states, animations and timing

Design principles (rules for the LLM)
-----------------------------------
1. Determinism first: when rendering pixel or layout values use exact numbers from the tokens below.
2. Do not invent colors/spacing/fonts outside the tokens — use tokens or explicit hex values only.
3. Localize only textual content via provided localization keys; never inline raw copy except examples.
4. Accessibility: every interactive element must have an ARIA label or role and keyboard focus style.
5. Stateless CSS: visual variations are implemented via CSS classes (e.g., `.active`, `.disabled`).
6. Avoid platform-specific APIs — produce plain HTML/CSS/JS contracts that map 1:1 to React/Vue/Svelte components.

Design tokens (canonical values)
--------------------------------
-- Colors
- --mx-purple: #1A0040 (brand primary)
- --mx-purple-600: #4338CA
- --mx-orange: #F59235 (brand accent)
- --bg-100: #F3F4FF (stage background)
- --card-bg: #FFFFFF
- --muted-600: #64748B
- --text-900: #0F172A
- --border-100: rgba(15,23,42,0.06)
- --chip-bg: #EEF2FF
- --chip-text: #3730A3
- --success: #10B981
- --warning: #F59E0B
- --danger: #EF4444

-- Typography
- font-family-heading: 'Raleway', system-ui, -apple-system, 'Segoe UI', sans-serif
- font-family-body: 'Space Grotesk', Inter, system-ui, -apple-system, 'Segoe UI', sans-serif
- font-weight-regular: 400
- font-weight-medium: 600
- font-weight-bold: 700

-- Spacing / scale (all units in px)
- S0 = 4; S1 = 8; S2 = 12; S3 = 16; S4 = 20; S5 = 24; S6 = 32; S7 = 40; S8 = 48

-- Radii
- r-sm: 8
- r-md: 18
- r-lg: 32

-- Elevation / Shadows
- shadow-1: 0 8px 24px rgba(15,23,42,0.06)

-- Breakpoints
- bp-md: 1080px (below stacks layout vertically)

Layout (global)
----------------
- Page uses a two-column app shell: left sidebar fixed width 280px, right content fills remaining width.
- Top-level HTML structure (semantic):

  <div class="app-shell" role="application">
    <aside class="sidebar" role="navigation">...</aside>
    <main class="main-grid"> ... </main>
  </div>

- Max content width inside main grid is fluid; grid columns inside `main-grid`: 1.4fr (stage) and 0.9fr (assistant panel) with 24px gap.
- Sidebar: background `--mx-purple`, padding S6 (32px). Profile area anchored to bottom.

Exact metrics
-------------
- Sidebar width: 280px
- Nav top bar height (if present): 48px
- Stage hero card min-height: 560px
- Stage card border-radius: r-lg (32px)
- Panel card padding: S5 (24px) to S6 (32px) depending on block

Localization (i18n)
-------------------
All textual content must be referenced by keys. Provide `locales/{lang}.json` files with flat key-value pairs.

Example `locales/en.json`:

{
  "app.title": "Maverx AI Training Builder",
  "nav.getting_started": "Getting Started",
  "nav.support": "Support",
  "nav.settings": "Settings",
  "intake.q1.title": "What is the topic or skill to be trained?",
  "intake.q1.badge": "AI",
  "action.generate_deck": "Generate Training Deck",
  "notes.placeholder": "Speaker notes for the selected slide will appear here."
}

Rules for LLMs: always substitute keys using the chosen language file; do not hardcode English strings into the layout.

Component Contracts (definitive)
--------------------------------
Each component defined below includes: filename suggestion, required props, DOM skeleton, ARIA roles, events, and expected behavior.

1) `Sidebar` — `Sidebar.jsx` (or equivalent)
- Props: `user: {name, initials}`, `links: [{key, href}]`
- DOM:

  <aside class="sidebar" role="navigation" aria-label="Main navigation">
    <div class="brand"> <div class="brand-logo">M</div> <div class="brand-title">{{app.title}}</div> </div>
    <nav class="nav-links" aria-label="Sections">
      <a class="nav-link" href="#">{{nav.getting_started}}</a>
      ...
    </nav>
    <div class="profile" aria-hidden="false"> ... </div>
  </aside>

- Behavior: Links must be tabbable; hover state uses `box-shadow` and background overlay rgba(255,255,255,0.06).

2) `Stage` (Slide Viewer area) — `Stage.jsx`
- Props: `slides`, `activeSlide`, `deckTitle`
- DOM: a card with hero area and slide preview placeholder. Use the following exact structure:

  <section class="hero-card" role="region" aria-label="Slide viewer">
    <div class="hero-icon" aria-hidden="true">✨</div>
    <h1 class="hero-title">{{stage.title}}</h1>
    <p class="hero-text">{{stage.subtitle}}</p>
  </section>

- Visual: center-aligned content; title font-size: 34px; subtitle color `--muted-600`.

3) `AssistantPanel` — `AssistantPanel.jsx` (right column)
- Props: `phase`, `step`, `messages`, `onSend`, `onApproveBlock`.
- DOM layout: header with progress dots, question block, chip row, textarea, action row.

Exact progress dots
-------------------
- Render 5 dots horizontally.
- Each dot is 10px diameter, 8px gap.
- Active dot: background `--mx-purple-600`; completed dot: `--mx-orange`; pending dot: `--border-100`.

Chip buttons
------------
- DOM: buttons with class `chip`.
- Size: padding 12px 16px, border-radius r-md (18px).
- Active state: background `--mx-purple-600`, text white.
- Behavior: clicking sets the chip `.active` class and emits `onSend({type:'chip', value})`.

Input area
----------
- Textarea with class `textarea-field`, min-height 92px, rounded r-md, border 1px solid `--border-100`.
- Enter key behavior: `Enter` sends message (unless `Shift+Enter`), mapped by `onSend(text)`.

Action button
-------------
- Primary button `.primary-button` uses linear-gradient(#4338CA, #8B5CF6), padding S4-S5.
- Disabled state: `opacity: 0.55; cursor: not-allowed`.

4) `Notes` — Speaker notes area
- Props: `notesText`
- DOM: `<div class="note-output" role="region" aria-label="Speaker notes">` with pre-wrapped text.

Behavior & State Machine (deterministic)
----------------------------------------
The frontend must implement the state machine described in the original `FRONTEND.md` attachments. Provide event names and payloads exactly as below so backend and LLM mocks can integrate reliably.

Key events (frontend emits / listens):
- `validateIntake(answers, step)` → expects `{ valid: boolean, followUp?: string }`
- `generateOutline(answers)` → expects `{ outline: Block[] }`
- `proposeBlock(answers, outline, blockIndex)` → expects `{ proposal: BlockProposal }`
- `generateBlock(answers, outline, blockIndex, proposal, styleGuide)` → returns `{ job_id }`, then poll `GET /block-status/:job_id` → `{ done, slides, slide_count }`
- `finalise(job_ids, answers, styleGuide)` → `{ download_url, title }`

Data shapes (JSON schemas)
--------------------------
Block (example):

{
  "block_id": "kickoff",
  "title": "Opening / Kick-off",
  "description": "Short opening activities and context",
  "slide_count_estimate": 4
}

BlockProposal:

{
  "block_id": "kickoff",
  "summary": "I will create 4 slides covering X, Y, Z",
  "slide_count": 4,
  "key_points": ["X","Y","Z"]
}

Slide:

{
  "slide_number": 1,
  "layout": "title_slide",
  "title": "Welcome",
  "body": "...",
  "module_block": "kickoff",
  "confidence": 0.93
}

Localization keys (complete list)
--------------------------------
Provide these keys in locale files (used by Chat, UI labels, chips, and tooltips):

- app.title
- nav.getting_started
- nav.support
- nav.settings
- intake.question.{0..4}.title
- intake.question.{0..4}.help
- intake.option.supply_outline
- intake.option.ai_outline
- chip.prompt_engineering
- chip.ai_literacy
- chip.ai_productivity
- chip.responsible_ai
- action.generate_deck
- notes.placeholder

Rendering rules for multi-language parity
----------------------------------------
1. Layout must be resilient to longer text (e.g., Dutch) — wrap copy inside flexible containers but preserve token-based paddings and fixed element sizes (sidebar width, dot sizes, icon sizes).
2. For fonts that differ per language, the LLM must substitute `font-family-heading` and `font-family-body` tokens only via the style guide injection point; never change spacing tokens.
3. Measurements used for vertical rhythm (line-height, margins) are unit-based from tokens; change only when explicit style guide entry overrides them.

Animations
----------
- Progress dot pulse: scale 1 → 1.08 → 1, duration 1000ms ease-in-out for active state.
- Chip hover: lift (translateY -2px) and box-shadow = shadow-1, duration 160ms.
- Slide generation placeholder shimmer: linear-gradient background animation 1200ms infinite.

Accessibility
-------------
- All interactive elements: keyboard focus visible outline `2px solid rgba(99,102,241,0.9)`.
- Color contrast: ensure text uses `--text-900` on `--card-bg` or `--chip-text` on `--chip-bg` to meet WCAG AA.
- Provide `aria-live=\"polite\"` on chat/history updates.

Implementation recipe for an LLM to generate the UI
--------------------------------------------------
1. Read the tokens and use them verbatim in CSS variables at the top of the stylesheet.
2. Create the HTML skeleton using the exact DOM structure outlined above. Use the exact class names.
3. Implement components as decoupled units with the props described. Each component must expose the events exactly as named.
4. Localize all textual content by replacing keys from a locale JSON file.
5. Respect the state machine event names and payloads; use the JSON schemas for generating mock responses when `VITE_MOCK_API=true`.
6. When generating CSS, prioritize the tokens and exact pixel values above.

Deliverables (files to include in any implementation)
---------------------------------------------------
- `index.html` (shell) that loads the app and locale JSON for a default language (e.g., `en`).
- `styles.css` containing all tokens as CSS variables and the full stylesheet.
- `components/Sidebar.*`, `components/Stage.*`, `components/AssistantPanel.*`, `components/Notes.*` (one file per component).
- `locales/en.json` and `locales/nl.json` (empty translations are acceptable but keys must exist).
- `api/mock.js` implementing the deterministic mock contract described in this file.
- `README.md` with run instructions and environment variables.

Examples
--------
Example minimal HTML skeleton (LLM can output this verbatim):

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>{{app.title}}</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <div class="app-shell" role="application">
      <aside class="sidebar" role="navigation" aria-label="Main navigation">...</aside>
      <main class="main-grid">...</main>
    </div>
    <script src="app.js"></script>
  </body>
</html>

Final notes
-----------
This spec is intentionally prescriptive: any LLM or frontend engineer that follows the tokens, DOM structure, class names, component contracts and localization keys will produce the same UI layout and behavior regardless of the underlying framework or language. If you want, I can also generate a ready-to-run React + Vite skeleton that implements this spec with mock endpoints.
