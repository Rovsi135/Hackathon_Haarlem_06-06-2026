import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from style_config import STYLE_GUIDE_PROMPT

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

def style_slides(slides_init_json: dict) -> dict:
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=16000,
        messages=[
            {"role": "system", "content": STYLE_GUIDE_PROMPT},
            {
                "role": "user",
                "content": f"Enrich this slide JSON with visual design decisions:\n\n{json.dumps(slides_init_json, indent=2)}"
            }
        ]
    )

    raw = response.choices[0].message.content
    # Extract JSON object robustly — ignore any preamble or trailing text
    start = raw.find('{')
    end = raw.rfind('}')
    return json.loads(raw[start:end + 1])


if __name__ == "__main__":
    with open("../content_generator/slides_init_text.json", "r", encoding="utf-8") as f:
        slides_init = json.load(f)

    styled = style_slides(slides_init)

    with open("slides_pre_styled.json", "w", encoding="utf-8") as f:
        json.dump(styled, f, indent=2)

    print(f"Done — {len(styled['slides'])} slides styled.")