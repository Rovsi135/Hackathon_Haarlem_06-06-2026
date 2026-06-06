"""
validate_slides.py
------------------
Pass 2 of the pptx pipeline.

Input:  slides_pre_styled.json  (output of style_slides.py)
Output: slides_feedback.json    (structured feedback to feed back into the content/styling LLM)
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from style_config import (
    BLOCK_COLORS,
    COLORS,
    CONTENT_RULES,
    DIDACTIC_BLOCKS,
    REQUIRED_SLIDE_TYPES,
    FONTS,
)

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

VALIDATOR_PROMPT = f"""
You are a strict quality validator for Maverx training presentations.

You will receive a slide JSON that has already gone through a styling pass.
Your job is to find every problem in it and return a structured feedback report.

You check three categories:

## 1. STRUCTURAL CHECKS
- Is there exactly one cover slide, and is it at index 0?
- Does the deck follow the required block order: cover → agenda → kickoff → theory → example → exercise → wrapup?
- Are all required slide types present: cover, agenda, timetable, kickoff, wrapup?
- Are there any blocks missing entirely?

## 2. STYLE COMPLIANCE CHECKS
Compare each slide's bg_color, title_color, and accent_color against these EXACT rules.
Do not accept freestyle color decisions — the colors must match:

Block color rules (bg_color → title_color → accent_color):
- cover:     #1A0040 → #F2F2F2 → #EF4453
- agenda:    #F2F2F2 → #0D006A → #3F0576
- kickoff:   #EDE9FF → #0D006A → #3F0576
- theory:    #F2F2F2 → #0D006A → (teal #00B0F0 or orange #F48A28 — either is acceptable)
- example:   #E7F9FF → #0D006A → #00B0F0
- exercise:  #FDEBDB → #0D006A → #F48A28
- wrapup:    #EDE9FF → #0D006A → #3F0576
- section:   #1A0040 → #F2F2F2 → #BCB3FF
- timetable: #F2F2F2 → #0D006A → #3F0576
- break:     #1A0040 → #F2F2F2 → #F7B8C0
- debrief:   #FEF0F1 → #0D006A → #EF4453

Flag any slide where the colors deviate from these rules.

## 3. CONTENT RULES CHECKS
- Any slide with more than {CONTENT_RULES["max_bullets_per_slide"]} bullets must have split_required: true
- Any slide with split_required: true must include a split_suggestion field explaining how to split it
- Slides in blocks {CONTENT_RULES["key_takeaway_required_for"]} must have use_key_takeaway: true
- Titles must be {CONTENT_RULES["max_title_words"]} words or fewer — flag any that exceed this
- Bullet text must not exceed {CONTENT_RULES["max_words_per_bullet"]} words — flag any that exceed this
- No bullet should start with a bullet symbol (•)

## 4. SCHEMA CHECKS
Every slide object must have ALL of these fields:
slide_index, block, title, bullets, speaker_notes, layout_key, bg_color, title_color, accent_color, use_key_takeaway, split_required

speaker_notes must have ALL of these sub-fields:
aim, time, instructions, reflective_question, debrief

Flag any slide missing any field.

---

## OUTPUT FORMAT

Return ONLY valid JSON in this exact structure. No markdown, no explanation, no preamble.

{{
  "summary": {{
    "total_slides": <int>,
    "total_issues": <int>,
    "has_blocking_issues": <bool>,
    "blocking_issues": ["<description of issues that must be fixed before rendering>"]
  }},
  "issues": [
    {{
      "slide_index": <int or null if structural>,
      "category": "structural" | "style" | "content" | "schema",
      "severity": "blocking" | "warning",
      "field": "<field name with the problem>",
      "current_value": "<what it currently is>",
      "expected_value": "<what it should be>",
      "fix_instruction": "<exact instruction to fix this, written so another LLM can act on it>"
    }}
  ],
  "correction_prompt": "<A complete prompt you would send to the styling LLM to fix all issues. Write it as if you are instructing the LLM directly, referencing slide indices and specific fields.>"
}}

The correction_prompt field is the most important output.
It must be a complete, self-contained instruction that the styling LLM can act on to produce a corrected slides_styled.json.
Reference every issue by slide_index and field name. Be specific and direct.
"""


def run_rule_checks(slides: list) -> list:
    issues = []
    required_fields = [
        "slide_index", "block", "title", "bullets", "speaker_notes",
        "layout_key", "bg_color", "title_color", "accent_color",
        "use_key_takeaway", "split_required"
    ]
    required_note_fields = ["aim", "time", "instructions", "reflective_question", "debrief"]

    # Block order check
    blocks_seen = [s.get("block") for s in slides]
    actual_order = [b for b in blocks_seen if b in DIDACTIC_BLOCKS]
    seen = set()
    deduped = []
    for b in actual_order:
        if b not in seen:
            seen.add(b)
            deduped.append(b)

    if deduped != DIDACTIC_BLOCKS[:len(deduped)]:
        issues.append({
            "slide_index": None,
            "category": "structural",
            "severity": "blocking",
            "field": "block_order",
            "current_value": str(deduped),
            "expected_value": str(DIDACTIC_BLOCKS),
            "fix_instruction": f"Reorder slides so blocks appear in this sequence: {DIDACTIC_BLOCKS}"
        })

    # Required slide types
    blocks_present = set(s.get("block") for s in slides)
    for required_block, required in REQUIRED_SLIDE_TYPES.items():
        if required and required_block not in blocks_present:
            issues.append({
                "slide_index": None,
                "category": "structural",
                "severity": "blocking",
                "field": "missing_block",
                "current_value": "absent",
                "expected_value": required_block,
                "fix_instruction": f"Add a '{required_block}' slide. This block is required in every deck."
            })

    for slide in slides:
        idx = slide.get("slide_index", "?")
        block = slide.get("block", "")

        # Missing top-level fields
        for field in required_fields:
            if field not in slide:
                issues.append({
                    "slide_index": idx,
                    "category": "schema",
                    "severity": "blocking",
                    "field": field,
                    "current_value": "missing",
                    "expected_value": "present",
                    "fix_instruction": f"Add the '{field}' field to slide {idx}."
                })

        # Missing speaker_note fields
        notes = slide.get("speaker_notes", {})
        for nf in required_note_fields:
            if nf not in notes:
                issues.append({
                    "slide_index": idx,
                    "category": "schema",
                    "severity": "blocking",
                    "field": f"speaker_notes.{nf}",
                    "current_value": "missing",
                    "expected_value": "present",
                    "fix_instruction": f"Add the '{nf}' field to speaker_notes on slide {idx}."
                })

        # Bullet count
        bullets = slide.get("bullets", [])
        if len(bullets) > CONTENT_RULES["max_bullets_per_slide"]:
            if not slide.get("split_required", False):
                issues.append({
                    "slide_index": idx,
                    "category": "content",
                    "severity": "blocking",
                    "field": "split_required",
                    "current_value": "false",
                    "expected_value": "true",
                    "fix_instruction": f"Slide {idx} has {len(bullets)} bullets (max {CONTENT_RULES['max_bullets_per_slide']}). Set split_required to true and add a split_suggestion field."
                })

        # Title word count
        title = slide.get("title", "")
        if len(title.split()) > CONTENT_RULES["max_title_words"]:
            issues.append({
                "slide_index": idx,
                "category": "content",
                "severity": "warning",
                "field": "title",
                "current_value": title,
                "expected_value": f"Max {CONTENT_RULES['max_title_words']} words",
                "fix_instruction": f"Shorten the title on slide {idx} to {CONTENT_RULES['max_title_words']} words or fewer. Current: '{title}'"
            })

        # Color compliance
        if block in BLOCK_COLORS:
            expected = BLOCK_COLORS[block]
            expected_bg    = COLORS.get(expected["bg"],    expected["bg"])
            expected_title = COLORS.get(expected["title"], expected["title"])

            actual_bg    = slide.get("bg_color", "")
            actual_title = slide.get("title_color", "")

            if actual_bg.upper() != expected_bg.upper():
                issues.append({
                    "slide_index": idx,
                    "category": "style",
                    "severity": "blocking",
                    "field": "bg_color",
                    "current_value": actual_bg,
                    "expected_value": expected_bg,
                    "fix_instruction": f"Set bg_color on slide {idx} (block: {block}) to {expected_bg}."
                })

            if actual_title.upper() != expected_title.upper():
                issues.append({
                    "slide_index": idx,
                    "category": "style",
                    "severity": "blocking",
                    "field": "title_color",
                    "current_value": actual_title,
                    "expected_value": expected_title,
                    "fix_instruction": f"Set title_color on slide {idx} (block: {block}) to {expected_title}."
                })

        # Key takeaway required
        if block in CONTENT_RULES["key_takeaway_required_for"]:
            if not slide.get("use_key_takeaway", False):
                issues.append({
                    "slide_index": idx,
                    "category": "content",
                    "severity": "warning",
                    "field": "use_key_takeaway",
                    "current_value": "false",
                    "expected_value": "true",
                    "fix_instruction": f"Slide {idx} is a '{block}' block — set use_key_takeaway to true and add a KEY TAKEAWAY bullet."
                })

    return issues


def validate_with_llm(slides_json: dict, rule_issues: list) -> dict:
    pre_check_summary = f"""
The following issues were already found by automated rule checks.
Do NOT re-report these as new issues. Use them as context when writing the correction_prompt.

Pre-detected issues ({len(rule_issues)} total):
{json.dumps(rule_issues, indent=2)}
"""

    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-5",
        max_tokens=8000,
        messages=[
            {"role": "system", "content": VALIDATOR_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{pre_check_summary}\n\n"
                    f"Now validate this full slide JSON:\n\n"
                    f"{json.dumps(slides_json, indent=2)}"
                )
            }
        ]
    )

    raw = response.choices[0].message.content
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)


def validate_slides(input_path: str = "slides_pre_styled.json") -> dict:
    print(f"[1/3] Loading {input_path}...")
    with open(input_path, "r") as f:
        slides_json = json.load(f)

    slides = slides_json.get("slides", [])
    print(f"      {len(slides)} slides loaded.")

    print("[2/3] Running rule-based checks...")
    rule_issues = run_rule_checks(slides)
    print(f"      {len(rule_issues)} rule issues found.")

    print("[3/3] Running LLM validation pass...")
    llm_result = validate_with_llm(slides_json, rule_issues)

    llm_result["summary"]["total_issues"] = (
        len(llm_result.get("issues", [])) + len(rule_issues)
    )

    return llm_result


if __name__ == "__main__":
    feedback = validate_slides("slides_pre_styled.json")

    with open("slides_feedback.json", "w") as f:
        json.dump(feedback, f, indent=2)
    print(f"\n✓ Feedback written to slides_feedback.json")
    print(f"  Total issues:  {feedback['summary']['total_issues']}")
    print(f"  Blocking:      {feedback['summary']['has_blocking_issues']}")

    print("\n--- CORRECTION PROMPT ---")
    print(feedback.get("correction_prompt", "No correction prompt generated."))
    print("-------------------------")