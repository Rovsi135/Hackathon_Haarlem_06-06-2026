import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent


def run_step(label: str, script: Path, cwd: Path) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, str(script)], cwd=str(cwd))
    if result.returncode != 0:
        sys.exit(f"\nPipeline stopped: '{label}' failed (exit {result.returncode}).")


def main() -> None:
    content_dir = BASE / "content_generator"
    pptx_dir    = BASE / "pptx_generator"

    # Step 1 — generate raw slide JSON
    run_step("Step 1/3  Generate slide content", content_dir / "slides_json_generator.py", content_dir)

    # Step 2 — generate pre-bite and post-bite documents
    run_step("Step 2/3  Generate bites", content_dir / "generate_bites.py", content_dir)

    # Step 3 — apply Maverx visual styling
    run_step("Step 3/3  Style slides (pass 1)", pptx_dir / "styling_first_pass.py", pptx_dir)

    print("\nAll done! Check pptx_generator/ and content_generator/ for outputs.")


if __name__ == "__main__":
    main()