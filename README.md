# Maverx AI Training Builder

> **Hackathon Haarlem — 06-06-2026**
> Transform a one-sentence training idea into a fully styled, editable PowerPoint deck in minutes.

---

## What It Does

You describe a training topic in plain language. The system:

1. Asks five structured intake questions (topic, audience, knowledge level, duration, learning objective)
2. Validates each answer with an AI agent until all fields meet quality thresholds
3. Generates structured slide content following Maverx's didactic model
4. Renders a polished `.pptx` in Maverx house style — ready to deliver or edit
5. Produces pre-bite and post-bite `.docx` documents as supplementary materials

The frontend runs entirely offline (mock API) for demos; the full pipeline requires an OpenRouter API key.

---

## Architecture Overview

```
User (browser)
  |
  v
Frontend (React + Vite)
  |  5-question intake form with validation loop
  |  Slide preview, speaker notes, confidence scores
  |  Download: .pptx + pre_bite.docx + post_bite.docx
  |
  v
Intake Validation Agent
  |  LLM checks completeness and quality
  |  Loops until all five fields pass
  |
  v
Content Generator
  |  LLM produces slide JSON from validated intake
  |  Enforces didactic model (Cover -> Agenda -> Kick-off -> Theory -> Example -> Exercise -> Wrap-up)
  |
  v
Styling Passes
  |  LLM applies Maverx design rules (colors, fonts, layouts)
  |  Rule validation flags blocking / warning issues
  |
  v
PPTX Renderer
   Loads Maverx master template, populates placeholders
   Outputs training_deck.pptx + bites
```

---

## Project Structure

```
.
+-- frontend/                   React + Vite UI (intake form, slide viewer)
+-- content_generator/          Python: LLM -> structured slide JSON + .docx bites
+-- pptx_generator/             Python: JSON -> styled .pptx via python-pptx
+-- first agent/                Python: CLI-based sequential intake validator
+-- second agent/               Python: Advanced LLM intake orchestrator
+-- main.py                     Entry point (wraps run_powerpoint_pipeline.py)
+-- run_powerpoint_pipeline.py  Full pipeline orchestrator (intake -> .pptx)
+-- ARCHITECTURE.md             Detailed system design, data flow, risk register
+-- .env                        OpenRouter API key (not committed)
```

---

## Didactic Model

Every generated training deck follows this fixed block sequence:

| Block    | Slides | Purpose                              |
|----------|--------|--------------------------------------|
| Cover    | 1      | Title and promise                    |
| Agenda   | 1      | High-level flow                      |
| Kick-off | 2-3    | Learning goals, energizer            |
| Theory   | 4-6    | Core concepts at the right level     |
| Example  | 2-4    | Concrete illustrations               |
| Exercise | 3-4    | Active application                   |
| Wrap-up  | 2-3    | Takeaways, next steps                |
| Post-bite| .docx  | Follow-up assignments                |

Each slide also carries five speaker-note fields: **aim**, **time**, **instructions**, **key discussion points**, and **debrief**.

---

## Tech Stack

| Layer            | Technology                                      |
|------------------|-------------------------------------------------|
| Frontend         | React 18, Vite 5, bilingual EN/NL (i18n)       |
| AI / LLM         | OpenRouter API - Claude Sonnet 4.6              |
| Content pipeline | Python 3, `openai` SDK                          |
| Presentation     | `python-pptx` (loads Maverx master template)    |
| Documents        | `python-docx` (pre/post-bite)                   |
| Configuration    | `house_style.yaml`, JSON schemas                |
| Environment      | Conda, `.env`                                   |

---

## Getting Started

### Prerequisites

- **Node.js** >= 18 + npm (frontend)
- **Python** >= 3.8 (backend pipeline)
- **Fonts:** Space Grotesk, Raleway (install system-wide for correct rendering)
- **OpenRouter API key** -> add to `.env`:

```
OPENROUTER_API_KEY=sk-or-...
```

### Run the Frontend (offline demo - no API key needed)

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. Uses the built-in mock API - no backend required.

### Run the Full Pipeline

```bash
# Install Python dependencies
pip install openai python-pptx python-docx pyyaml python-dotenv

# Run with a sample intake file
python main.py --intake content_generator/validated_input.json --output pptx_generator/training_deck.pptx
```

**CLI options for `run_powerpoint_pipeline.py`:**

| Flag               | Description                                       |
|--------------------|---------------------------------------------------|
| `--intake <file>`  | Path to validated intake JSON                     |
| `--output <file>`  | Output .pptx path                                 |
| `--render-existing`| Skip content generation, re-render existing JSON  |
| `--style-guide`    | Path to alternate house style YAML                |

---

## Output Artifacts

| File                  | Description                                      |
|-----------------------|--------------------------------------------------|
| `training_deck.pptx`  | Fully styled, editable PowerPoint deck           |
| `pre_bite.docx`       | Pre-training preparation document                |
| `post_bite.docx`      | Post-training assignments and reflection         |

---

## Maverx House Style (Design Tokens)

| Token              | Value                                     |
|--------------------|-------------------------------------------|
| Primary dark       | `#0D006A`                                 |
| Deep purple        | `#3F0576`                                 |
| Rose red           | `#EF4453`                                 |
| Orange             | `#F48A28`                                 |
| Teal               | `#00B0F0`                                 |
| Cover background   | `#1A0040`                                 |
| Default background | `#F2F2F2`                                 |
| Primary font       | Space Grotesk (fallback: Calibri)         |
| Title size         | 33pt Bold                                 |
| Body bullets       | 15pt min, max 6 per slide, max 20 words   |
| Title length       | max 8 words                               |

Full brand specification: [pptx_generator/house_style.yaml](pptx_generator/house_style.yaml)

---

## Configuration

- **API key:** `.env` -> `OPENROUTER_API_KEY`
- **Brand style:** `pptx_generator/house_style.yaml` (single source of truth)
- **Design tokens (Python):** `pptx_generator/style_config.py`
- **Frontend mock vs real API:** `frontend/src/api/client.js` -> toggle `USE_MOCK`
- **Localization strings:** `frontend/src/locales/en.json` / `nl.json`

---

## Frontend Features

- Guided 5-step intake form with per-field validation feedback
- Live run-cost meter
- Per-slide confidence badge
- Slide viewer with speaker notes panel
- Progress dots navigation
- Bilingual UI (English / Dutch)
- One-click download bundle

---

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - Full system design, data flow, team split, critical path, and risk register
- [frontend/README.md](frontend/README.md) - Frontend-specific setup and component contracts
