import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(dotenv_path=ROOT_DIR / ".env")

SYSTEM_PROMPT = """
You are a professional training designer for Maverx, a Dutch consultancy.
You generate structured PowerPoint slide content following a strict didactic model.

DIDACTIC MODEL — every training must follow this block order exactly:
1. Cover: title and promise (1 slide)
2. Agenda: high-level flow (1 slide)
3. Timetable: trainer-facing timing overview (1 slide)
4. Kick-off: learning goals and energizer (2-3 slides)
5. Theory: core concepts explained for the audience level (4-6 slides)
6. Example: concrete recognizable illustration of the theory (3-4 slides)
7. Exercise: active application, individual or group work (3-4 slides)
8. Wrap-up: key takeaways, link to practice, next steps (2-3 slides)

RULES:
- Scale slide count to the training duration
- Match tone and complexity to the knowledge level
- Bullets must be concrete and actionable, not generic filler
- Never write generic placeholders like 'overview of concepts' or 'key takeaways' — write the actual content
- Every slide must have all 5 speaker note fields
- Output ONLY valid JSON, no markdown, no explanation, no preamble

OUTPUT FORMAT:
{
  "slides": [
    {
      "slide_index": 0,
      "block": "cover",
      "title": "...",
      "bullets": ["...", "..."],
      "speaker_notes": {
        "aim": "...",
        "time": "...",
        "instructions": "...",
        "reflective_question": "...",
        "debrief": "..."
      }
    }
  ]
}
"""


def normalize_intake(intake: dict) -> dict:
    """Accept both the second-agent schema and the older validated_input schema."""
    duration_minutes = intake.get("duration_minutes")
    duration_hours = intake.get("duration_hours")
    if duration_minutes is None and duration_hours is not None:
        duration_minutes = int(float(duration_hours) * 60)
    if duration_hours is None and duration_minutes is not None:
        duration_hours = round(int(duration_minutes) / 60, 2)

    return {
        "topic": intake.get("topic", ""),
        "audience": intake.get("target_audience") or intake.get("audience", ""),
        "knowledge_level": intake.get("knowledge_level", "beginner"),
        "duration_minutes": int(duration_minutes or 180),
        "duration_hours": duration_hours or 3,
        "learning_objective": (
            intake.get("primary_learning_objective")
            or intake.get("learning_objective")
            or ""
        ),
    }


def extract_json(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.removeprefix("```json").removeprefix("```")
        clean = clean.removesuffix("```").strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end = clean.rfind("}")
        if start == -1 or end == -1:
            raise
        return json.loads(clean[start:end + 1])


def generate_slides_from_intake(intake: dict, client: OpenAI | None = None) -> dict:
    normalized = normalize_intake(intake)
    llm_client = client or OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )

    user_prompt = f"""
Generate a complete training slide deck for the following intake:

Topic: {normalized['topic']}
Audience: {normalized['audience']}
Knowledge level: {normalized['knowledge_level']}
Duration: {normalized['duration_minutes']} minutes
Learning objective: {normalized['learning_objective']}

Generate all slides following the didactic model. Scale slide count to the duration.
"""

    response = llm_client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=16000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    slides = extract_json(response.choices[0].message.content)
    if "slides" not in slides:
        raise ValueError("Content generator returned JSON without a 'slides' key.")
    return slides


def main() -> None:
    input_path = BASE_DIR / "validated_input.json"
    output_path = BASE_DIR / "slides_init_text.json"

    with input_path.open("r", encoding="utf-8") as f:
        intake = json.load(f)

    slides = generate_slides_from_intake(intake)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(slides, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(slides['slides'])} slides.")


if __name__ == "__main__":
    main()
