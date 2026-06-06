"""
styling_iteration.py
--------------------
Orchestrator for Pass 3 of the pptx pipeline.

Reads slides_feedback.json and decides:
  - If feedback is CLEAN (no blocking issues) → call build_pptx() from teammate's file
  - If feedback has issues → send correction_prompt + style_config + slides_auto_fixed.json
    to the LLM, produce slides_fully_styled.json, then call build_pptx()

Input files:
  - slides_feedback.json      (from validate_slides.py)
  - slides_auto_fixed.json    (from validate_slides.py)
  - style_config.py           (imported directly)

Output:
  - slides_fully_styled.json  (corrected and ready for rendering)
  - calls build_pptx(slides_fully_styled.json) from pptx_builder.py
"""

import anthropic
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from style_config import STYLE_GUIDE_PROMPT

# ---------------------------------------------------------------------------
# Load env and client
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# Import teammate's pptx builder function
# ---------------------------------------------------------------------------
try:
    from pptx_builder import build_pptx
    PPTX_BUILDER_AVAILABLE = True
except ImportError:
    print("⚠ pptx_builder.py not found — will save slides_fully_styled.json but skip pptx generation.")
    PPTX_BUILDER_AVAILABLE = False

    def build_pptx(slides_json: dict):
        print("  [stub] build_pptx() called — pptx_builder.py not connected yet.")


# ---------------------------------------------------------------------------
# CORRECTION SYSTEM PROMPT
# ---------------------------------------------------------------------------
CORRECTION_SYSTEM_PROMPT = f"""
You are a Maverx slide JSON corrector.

You will receive:
1. A correction prompt describing exactly what needs to be fixed
2. The current slide JSON (already partially auto-fixed)

Your job is to apply every fix described in the correction prompt to the slide JSON
and return the complete corrected JSON.

Follow these style rules at all times:

{STYLE_GUIDE_PROMPT}

Additional rules:
- Do NOT remove or rename any existing fields
- Do NOT change any slide that is not mentioned in the correction prompt
- When adding new slides (cover, agenda, timetable), generate real content — no placeholder text
- When splitting a slide, create two complete slide objects with all required fields
- Maintain consecutive slide_index values with no gaps
- All speaker_notes must have: aim, time, instructions, reflective_question, debrief

Return ONLY valid JSON with the structure:
{{
  "slides": [ ... ]
}}

No markdown, no explanation, no preamble.
"""


# ---------------------------------------------------------------------------
# FEEDBACK EVALUATION
# ---------------------------------------------------------------------------

def is_feedback_clean(feedback: dict) -> bool:
    """Returns True if there are no blocking issues — safe to render."""
    summary = feedback.get("summary", {})
    has_blocking = summary.get("has_blocking_issues", True)
    blocking_list = summary.get("blocking_issues", [])
    issues = feedback.get("issues", [])
    blocking_issue_count = sum(1 for i in issues if i.get("severity") == "blocking")

    if has_blocking or blocking_list or blocking_issue_count > 0:
        return False
    return True


def feedback_report(feedback: dict) -> str:
    summary = feedback.get("summary", {})
    issues = feedback.get("issues", [])
    blocking = [i for i in issues if i.get("severity") == "blocking"]
    warnings = [i for i in issues if i.get("severity") == "warning"]
    auto_fixes = feedback.get("auto_fixes", [])

    return (
        f"  Total issues:  {summary.get('total_issues', '?')}\n"
        f"  Blocking:      {len(blocking)}\n"
        f"  Warnings:      {len(warnings)}\n"
        f"  Auto-fixes:    {len(auto_fixes)}\n"
        f"  Has blocking:  {summary.get('has_blocking_issues', '?')}"
    )


# ---------------------------------------------------------------------------
# CORRECTION LLM CALL
# ---------------------------------------------------------------------------

def apply_corrections(slides_json: dict, correction_prompt: str) -> dict:
    """Send the auto-fixed JSON + correction prompt to the LLM."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=CORRECTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"## Correction instructions\n\n"
                    f"{correction_prompt}\n\n"
                    f"## Current slide JSON to correct\n\n"
                    f"{json.dumps(slides_json, indent=2)}"
                )
            }
        ]
    )

    raw = response.content[0].text
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(clean)


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

def run_styling_iteration(
    feedback_path: str = "slides_feedback.json",
    auto_fixed_path: str = "slides_auto_fixed.json",
    output_path: str = "slides_fully_styled.json",
):
    print("=" * 55)
    print("STYLING ITERATION")
    print("=" * 55)

    # 1. Load feedback
    print(f"\n[1/4] Loading feedback from {feedback_path}...")
    with open(feedback_path, "r") as f:
        feedback = json.load(f)
    print(feedback_report(feedback))

    # 2. Decide: clean or needs correction
    if is_feedback_clean(feedback):
        print("\n✓ Feedback is clean — no blocking issues.")
        print(f"[2/4] Loading {auto_fixed_path} as final JSON...")
        with open(auto_fixed_path, "r") as f:
            final_json = json.load(f)

    else:
        print("\n✗ Blocking issues found — running correction pass...")
        correction_prompt = feedback.get("correction_prompt", "")

        if not correction_prompt:
            raise ValueError(
                "slides_feedback.json has blocking issues but no correction_prompt. "
                "Re-run validate_slides.py to regenerate feedback."
            )

        print(f"[2/4] Loading {auto_fixed_path}...")
        with open(auto_fixed_path, "r") as f:
            auto_fixed_json = json.load(f)

        print("[3/4] Sending to correction LLM...")
        corrected_json = apply_corrections(auto_fixed_json, correction_prompt)

        slide_count = len(corrected_json.get("slides", []))
        print(f"✓ Correction complete — {slide_count} slides.")
        final_json = corrected_json

    # 3. Save final JSON
    with open(output_path, "w") as f:
        json.dump(final_json, f, indent=2)
    print(f"\n[4/4] Final JSON saved to {output_path}")

    # 4. Call pptx builder
    print("\n→ Calling build_pptx()...")
    if PPTX_BUILDER_AVAILABLE:
        build_pptx(final_json)
        print("✓ build_pptx() completed.")
    else:
        print("  Skipped — connect pptx_builder.py to enable rendering.")

    print("\n" + "=" * 55)
    print("DONE")
    print("=" * 55)

    return final_json


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_styling_iteration(
        feedback_path="slides_feedback.json",
        auto_fixed_path="slides_auto_fixed.json",
        output_path="slides_fully_styled.json",
    )