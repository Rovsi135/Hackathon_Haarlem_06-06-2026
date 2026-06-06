import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
CONTENT_DIR = ROOT_DIR / "content_generator"
PPTX_DIR = ROOT_DIR / "pptx_generator"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(CONTENT_DIR))
sys.path.insert(0, str(PPTX_DIR))

from content_generator.slides_json_generator import generate_slides_from_intake
from pptx_generator.pptx_builder import build_pptx, normalize_slides_for_rendering
from pptx_generator.styling_first_pass import style_slides
from pptx_generator.validate_slides import run_rule_checks


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_rule_feedback(slides_json: dict) -> dict:
    issues = run_rule_checks(slides_json.get("slides", []))
    blocking = [issue for issue in issues if issue.get("severity") == "blocking"]
    return {
        "summary": {
            "total_slides": len(slides_json.get("slides", [])),
            "total_issues": len(issues),
            "has_blocking_issues": bool(blocking),
            "blocking_issues": [issue["fix_instruction"] for issue in blocking],
        },
        "issues": issues,
        "correction_prompt": "",
    }


def run_pipeline(
    intake_path: Path,
    output_path: Path,
    render_existing: Path | None = None,
    style_guide_path: Path | None = None,
) -> Path:
    if render_existing:
        print(f"[1/4] Loading existing slide JSON: {render_existing}")
        styled_slides = read_json(render_existing)
    else:
        print(f"[1/4] Loading intake: {intake_path}")
        styled_slides = generate_and_style(read_json(intake_path), style_guide_path)

    print("[4/4] Normalizing, validating, and rendering PPTX...")
    render_ready = normalize_slides_for_rendering(styled_slides)
    write_json(PPTX_DIR / "slides_render_ready.json", render_ready)
    write_json(PPTX_DIR / "slides_feedback.json", build_rule_feedback(render_ready))

    pptx_path = build_pptx(
        render_ready,
        output_path=output_path,
        render_ready_path=PPTX_DIR / "slides_render_ready.json",
    )
    print(f"      Wrote {pptx_path}")
    return pptx_path


def generate_and_style(intake: dict, style_guide_path: Path | None = None) -> dict:
    print("[2/4] Generating slide content...")
    slides_init = generate_slides_from_intake(intake)
    write_json(CONTENT_DIR / "slides_init_text.json", slides_init)
    print(f"      Wrote {CONTENT_DIR / 'slides_init_text.json'}")

    style_guide_content = None
    if style_guide_path:
        style_guide_content = style_guide_path.read_text(encoding="utf-8")

    print("[3/4] Applying Maverx styling pass...")
    styled_slides = style_slides(slides_init, style_guide_content=style_guide_content)
    write_json(PPTX_DIR / "slides_pre_styled.json", styled_slides)
    print(f"      Wrote {PPTX_DIR / 'slides_pre_styled.json'}")
    return styled_slides


def run_pipeline_from_intake(
    intake: dict,
    output_path: Path = PPTX_DIR / "training_deck.pptx",
    style_guide_path: Path | None = None,
) -> Path:
    styled_slides = generate_and_style(intake, style_guide_path)
    render_ready = normalize_slides_for_rendering(styled_slides)
    write_json(PPTX_DIR / "slides_render_ready.json", render_ready)
    write_json(PPTX_DIR / "slides_feedback.json", build_rule_feedback(render_ready))
    return build_pptx(
        render_ready,
        output_path=output_path,
        render_ready_path=PPTX_DIR / "slides_render_ready.json",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Maverx training PowerPoint from intake JSON.")
    parser.add_argument(
        "--intake",
        default=str(CONTENT_DIR / "validated_input.json"),
        help="Input intake JSON. Supports both second-agent and legacy schemas.",
    )
    parser.add_argument(
        "--output",
        default=str(PPTX_DIR / "training_deck.pptx"),
        help="Output .pptx path.",
    )
    parser.add_argument(
        "--render-existing",
        help="Skip LLM generation and styling, and render an existing slide JSON file.",
    )
    parser.add_argument(
        "--style-guide",
        help="Optional extracted style guide text file for the styling LLM.",
    )
    args = parser.parse_args()

    run_pipeline(
        intake_path=Path(args.intake),
        output_path=Path(args.output),
        render_existing=Path(args.render_existing) if args.render_existing else None,
        style_guide_path=Path(args.style_guide) if args.style_guide else None,
    )


if __name__ == "__main__":
    main()
