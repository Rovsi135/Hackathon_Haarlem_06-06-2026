#import anthropic
import json
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()


client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# Load validated intake from teammate's script
with open("validated_input.json", "r", encoding="utf-8") as f:
    intake = json.load(f)


system_prompt = """
You are a professional training designer for Maverx, a Dutch consultancy.
You generate structured PowerPoint slide content following a strict didactic model.

DIDACTIC MODEL — every training must follow this block order exactly:
1. Kick-off: learning goals, agenda, energizer (2-3 slides)
2. Theory: core concepts explained for the audience level (4-6 slides)
3. Example: concrete recognizable illustration of the theory (3-4 slides)
4. Exercise: active application, individual or group work (3-4 slides)
5. Wrap-up: key takeaways, link to practice, next steps (2-3 slides)

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
      "block": "kickoff",
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

user_prompt = f"""
Generate a complete training slide deck for the following intake:

Topic: {intake['topic']}
Audience: {intake['audience']}
Knowledge level: {intake['knowledge_level']}
Duration: {intake['duration_hours']} hours
Learning objective: {intake['learning_objective']}

Generate all slides following the didactic model. Scale slide count to the duration.
"""


response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-6",
    #model="openai/gpt-4o-mini",
    max_tokens=16000,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)


raw = response.choices[0].message.content


# Strip markdown code fences if model adds them despite instructions
if raw.strip().startswith("```"):
    raw = raw.strip()
    raw = raw.removeprefix("```json").removeprefix("```")
    raw = raw.removesuffix("```").strip()

try:
    slides = json.loads(raw)
except json.JSONDecodeError as e:
    print("JSON parse failed:", e)
    print("Raw output:", raw)
    raise
  
  
with open("slides_init_text.json", "w", encoding="utf-8") as f:
    json.dump(slides, f, indent=2, ensure_ascii=False)

print(f"Generated {len(slides['slides'])} slides.")