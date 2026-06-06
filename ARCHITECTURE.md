# Maverx AI Training Builder — Architecture

**Tier:** 1 (Single Training) — polish beats scope in 7 hours  
**Target:** One-sentence idea → editable .pptx in Maverx house style in <10 min

---

## System Overview

```
User (browser)
    │
    ▼
[Intake Form UI]  ←── Lovable (React)
    │  5 questions + follow-up loop
    ▼
[Intake Validator]  ←── OpenRouter API (Claude/GPT-4)
    │  Refuses to proceed until input is complete
    ▼
[Content Generator]  ←── OpenRouter API
    │  Returns structured JSON training plan
    ▼
[PPTX Renderer]  ←── python-pptx + Maverx master slides
    │  Populates layouts, injects speaker notes
    ▼
[Document Generator]  ←── python-docx
    │  Pre-bite + post-bite .docx files
    ▼
Download bundle (.pptx + 2x .docx)
```

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Frontend | Lovable (React) | Fast UI, your team knows it |
| Backend | Python + FastAPI | Best pptx/docx library support |
| AI | OpenRouter (Claude Sonnet) | Credits provided, structured output |
| PPTX | python-pptx | Opens + edits existing master slides |
| Docs | python-docx | Pre-bite / post-bite generation |
| Deploy | Any (Railway, Render, or localhost) | Just needs to demo |

---

## Data Flow — Step by Step

### Step 1: Intake (frontend)
Collect these 5 fields. Do NOT proceed until all are sufficiently filled.

```
1. topic          — "Prompt Engineering for Marketing"
2. audience       — "Marketing team, non-technical"
3. knowledge_level — beginner | intermediate | advanced
4. duration       — "3 hours"
5. learning_objective — "Participants can write effective AI prompts"
```

**Validation rule:** Send to AI validator. If any field is vague (e.g., topic = "AI stuff"), the validator returns follow-up questions. Loop until complete. Show a "readiness score" to the user.

---

### Step 2: Content Generation (AI → JSON)

Single prompt call to OpenRouter. Ask for structured JSON output.

**Output schema:**
```json
{
  "training_title": "",
  "total_duration_min": 180,
  "slide_count": 22,
  "prebite": {
    "title": "",
    "content": "",
    "type": "reading | install | reflection"
  },
  "postbite": {
    "title": "",
    "content": "",
    "assignments": []
  },
  "modules": [
    {
      "block": "kickoff | theory | example | exercise | wrapup",
      "title": "",
      "duration_min": 20,
      "slides": [
        {
          "slide_number": 1,
          "layout": "title_slide | content | two_col | agenda | exercise | quote",
          "title": "",
          "body": "",
          "table": null,
          "speaker_notes": {
            "aim": "",
            "time_indication": "",
            "instruction_steps": "",
            "reflective_question": "",
            "debrief_summary": ""
          }
        }
      ]
    }
  ]
}
```

**Critical:** Use `response_format: json` or function calling. Do NOT parse free text.

---

### Step 3: PPTX Rendering

**Key rule:** Load the Maverx master `.pptx` and USE its slide layouts. Do NOT create slides from scratch.

```python
from pptx import Presentation

# Load master
prs = Presentation("maverx_master.pptx")

# Map layout names to indices
layouts = {layout.name: i for i, layout in enumerate(prs.slide_layouts)}

# For each slide in JSON:
layout_idx = layouts.get(slide["layout"], 1)
slide_obj = prs.slides.add_slide(prs.slide_layouts[layout_idx])

# Populate placeholders
slide_obj.placeholders[0].text = slide["title"]
slide_obj.placeholders[1].text = slide["body"]

# Inject speaker notes (all 5 fields)
notes = slide_obj.notes_slide.notes_text_frame
notes.text = f"""
AIM: {slide["speaker_notes"]["aim"]}
TIME: {slide["speaker_notes"]["time_indication"]}
INSTRUCTIONS: {slide["speaker_notes"]["instruction_steps"]}
REFLECTIVE QUESTION: {slide["speaker_notes"]["reflective_question"]}
DEBRIEF: {slide["speaker_notes"]["debrief_summary"]}
"""
```

**First thing to do:** Open the master .pptx, print all layout names, map them to your JSON `layout` field. This must work before anything else.

---

### Step 4: Pre-bite & Post-bite

Generate as `.docx` using `python-docx`. Simple formatted documents.  
Include: title, intro paragraph, content, and a Maverx-styled header if possible.

---

## Slide Count by Block (for a 3-hour training ~22 slides)

| Block | Slides | Duration |
|-------|--------|----------|
| Kick-off | 3–4 | 15 min |
| Theory | 6–8 | 60 min |
| Example | 3–4 | 30 min |
| Exercise | 4–5 | 45 min |
| Wrap-up | 2–3 | 15 min |
| **Total** | **~22** | **~165 min** |

Scale proportionally for different durations.

---

## Team Split (7 hours)

| Person | Owns | Hours 0–3 | Hours 3–6 | Hour 6–7 |
|--------|------|-----------|-----------|----------|
| P1 | Frontend (Lovable) | Intake form UI + follow-up loop | Connect to backend API | Polish, error states |
| P2 | AI prompts | Intake validator prompt | Content generation prompt + JSON schema | Edge case testing |
| P3 | PPTX engine | Map master layouts, render pipeline | Speaker notes, tables | Edge cases |
| P4 | Docs + deploy | Pre-bite/post-bite generator | README + backend deploy | Demo prep |

---

## Critical Path (do these first, in order)

1. **[P3, Hour 0]** Open master .pptx, print layout names → confirm python-pptx can read and write it
2. **[P2, Hour 0]** Write intake validator prompt → test with vague input ("AI stuff")
3. **[P1, Hour 0]** Scaffold Lovable form with 5 fields + API call
4. **[P2, Hour 1]** Write content generation prompt → get valid JSON back
5. **[P3, Hour 2]** First end-to-end: JSON → .pptx renders with correct layouts
6. **[P4, Hour 2]** Pre-bite/post-bite renders as .docx
7. **[All, Hour 4]** Integration: full pipeline works end-to-end
8. **[All, Hour 5–6]** Polish: speaker notes formatting, error handling, README
9. **[All, Hour 6–7]** Demo prep + submission checklist

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Master .pptx layouts don't map cleanly | High | P3 starts here immediately. Have a fallback: hardcode the 3 most common layouts. |
| AI returns invalid JSON | Medium | Validate schema, retry once with error message in prompt |
| python-pptx font/color drift | Medium | Only set text content, never override theme colors |
| Intake loop never terminates | Low | Cap at 3 follow-up rounds, then allow proceed with warning |
| Demo fails live | Medium | Pre-generate a working example before the demo |

---

## API Prompt Strategy

### Intake Validator (fast, cheap model)
```
You are an intake validator for a training design system.
Given this intake form, identify any fields that are too vague to generate quality training content.
Return JSON: { "complete": true/false, "follow_up_questions": ["..."] }
Rules: refuse if topic is generic, audience is undefined, or objective is unmeasurable.
```

### Content Generator (use best model you have)
```
You are a professional instructional designer following the Maverx didactic model.
Generate a complete training plan as JSON following this exact schema: [schema]
Rules:
- Every training MUST include: kick-off → theory → example → exercise → wrap-up
- Speaker notes must have all 5 fields on every slide
- Slide count = roughly 7 slides per hour of training
- Never leave a field empty — always write real content
```

---

## Submission Checklist

- [ ] .pptx opens in PowerPoint without repair prompt
- [ ] All text is editable (no images of text)
- [ ] Maverx master layouts used, not recreated
- [ ] Speaker notes on every slide, all 5 fields
- [ ] Full didactic arc present
- [ ] Pre-bite .docx present
- [ ] Post-bite .docx present
- [ ] Intake asks 5 questions + handles vague input
- [ ] README with setup + run instructions
- [ ] Pre-generated demo example ready
