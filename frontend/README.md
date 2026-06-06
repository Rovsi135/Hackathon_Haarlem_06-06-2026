# Maverx AI Training Builder — Frontend

React + Vite UI for the Maverx AI Training Builder. Turns a one-sentence
training idea into a structured, editable PowerPoint in Maverx house style
through a guided, conversational intake.

The UI is a faithful implementation of [`../FRONTEND_L.md`](../FRONTEND_L.md)
(design tokens, component contracts, state-machine events) and covers the
business-case requirements: per-slide **confidence scoring**, a **run-cost
meter**, and **bilingual EN/NL** output.

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (default <http://localhost:5173>). It runs out of the box
on the built-in **mock API** — no backend required.

## How it works

The app drives a deterministic state machine:

```
intake (5 validated questions)
  → choose outline path (supply your own / AI research)
  → review the proposed outline (Maverx didactic model)
  → per block: SlideKick proposes → you approve → slides generate
  → review the deck (with confidence per slide + speaker notes)
  → finalise → download bundle (.pptx + pre-bite + post-bite)
```

- **Left sidebar** — brand, navigation, language switch, live run-cost meter.
- **Stage (centre)** — the artifact preview: hero → outline → slide canvas +
  filmstrip + speaker notes → download.
- **Assistant panel (right)** — SlideKick's questions, chips, proposals and
  action buttons, with the 5-dot progress indicator.

## Mock vs. real backend

The UI talks to a single API surface (`src/api/client.js`) that switches on the
`VITE_MOCK_API` flag:

| `VITE_MOCK_API` | Behaviour |
| --------------- | --------- |
| `true` (default) | Uses `src/api/mock.js` — deterministic, offline, mirrors the real intake validation rules. |
| `false` | Calls the FastAPI backend at `VITE_API_BASE` (default `/api`, proxied to `VITE_API_TARGET`). |

Copy `.env.example` to `.env` to configure:

```bash
cp .env.example .env
```

### Backend endpoints (when `VITE_MOCK_API=false`)

The client expects these routes (see `src/api/client.js`), matching the
state-machine events in `FRONTEND_L.md`:

| Event | Method & path | Response |
| ----- | ------------- | -------- |
| `validateIntake` | `POST /api/validate-intake` | `{ valid, normalized?, followUp? }` |
| `generateOutline` | `POST /api/generate-outline` | `{ outline: Block[] }` |
| `proposeBlock` | `POST /api/propose-block` | `{ proposal: BlockProposal }` |
| `generateBlock` | `POST /api/generate-block` | `{ job_id }` |
| block status | `GET /api/block-status/:job_id` | `{ done, slides, slide_count }` |
| `finalise` | `POST /api/finalise` | `{ download_url, title }` |

## Localization

All copy lives in `src/locales/en.json` and `src/locales/nl.json` as flat keys.
Switch language with the EN/NL toggle in the sidebar, or set the default with
`VITE_DEFAULT_LANG`. To add a language, drop in a new locale file and register
it in `src/i18n/index.js`.

## Project structure

```
frontend/
├── index.html
├── vite.config.js
├── .env.example
└── src/
    ├── main.jsx
    ├── App.jsx              # state machine orchestrator
    ├── styles.css           # all design tokens + stylesheet
    ├── i18n/index.js        # tiny localization hook
    ├── locales/{en,nl}.json
    ├── api/
    │   ├── client.js        # mock / real switch
    │   └── mock.js          # deterministic mock contract
    └── components/
        ├── Sidebar.jsx
        ├── Stage.jsx
        ├── AssistantPanel.jsx
        ├── Notes.jsx
        ├── ProgressDots.jsx
        └── ConfidenceBadge.jsx
```

## Build

```bash
npm run build     # outputs to dist/
npm run preview   # serve the production build locally
```
