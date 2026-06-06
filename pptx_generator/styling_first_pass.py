import json
import os
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from style_config import STYLE_GUIDE_PROMPT

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)


def build_style_messages(slides_init_json: dict, style_guide_content: str | None = None) -> list[dict]:
    slide_json_prompt = (
        "Enrich this slide JSON with visual design decisions:\n\n"
        f"{json.dumps(slides_init_json, indent=2)}"
    )

    if not style_guide_content:
        return [
            {"role": "system", "content": STYLE_GUIDE_PROMPT},
            {"role": "user", "content": slide_json_prompt},
        ]

    return [
        {
            "role": "system",
            "content": (
                "You are a visual design assistant for presentations. "
                "Use the style guide supplied by the user as the source of truth."
            ),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "STYLE_GUIDE_IMPORT:\n\n" + style_guide_content,
                },
                {
                    "type": "text",
                    "text": slide_json_prompt,
                },
            ],
        },
    ]


def style_slides(slides_init_json: dict, style_guide_content: str | None = None) -> dict:
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=16000,
        messages=build_style_messages(slides_init_json, style_guide_content),
    )

    raw = response.choices[0].message.content
    # Extract JSON object robustly — ignore any preamble or trailing text
    start = raw.find('{')
    end = raw.rfind('}')
    return json.loads(raw[start:end + 1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--style-guide",
        help="Optional extracted style guide text file to pass as STYLE_GUIDE_IMPORT.",
    )
    args = parser.parse_args()

    with open("../content_generator/slides_init_text.json", "r", encoding="utf-8") as f:
        slides_init = json.load(f)

    style_guide_content = None
    if args.style_guide:
        with open(args.style_guide, "r", encoding="utf-8") as f:
            style_guide_content = f.read()

    styled = style_slides(slides_init, style_guide_content=style_guide_content)

    with open("slides_pre_styled.json", "w", encoding="utf-8") as f:
        json.dump(styled, f, indent=2)

    print(f"Done — {len(styled['slides'])} slides styled.")
