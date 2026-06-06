"""
generate_bites.py
-----------------
Generates pre-bite and post-bite documents as .docx files using python-docx.

Input:  validated_input.json   (intake from the intake agent)
        slides_init_text.json  (generated slides content)
Output: pre_bite.docx
        post_bite.docx

Run this after slides_generator.py has completed.
"""

import json
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── Import style config from sibling pptx_generator directory ─────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "pptx_generator"))
try:
    from style_config import COLORS, FONTS
    FONT_PRIMARY  = FONTS.get("primary", "Calibri")
    FONT_FALLBACK = FONTS.get("fallback", "Calibri")

    def _hex(key: str) -> str:
        return COLORS.get(key, "#000000").lstrip("#")

    C_PURPLE    = _hex("dark_purple")
    C_BODY_BLUE = _hex("primary_dark")
    C_RED       = _hex("rose_red")
    C_TEAL      = _hex("teal")
    C_LIGHT     = _hex("light_purple")
    C_GREY      = _hex("dark_grey")
    C_WHITE     = "FFFFFF"

except ImportError:
    print("[WARN] style_config.py not found — using fallback Maverx colors.")
    FONT_PRIMARY  = "Calibri"
    FONT_FALLBACK = "Calibri"
    C_PURPLE    = "1A0040"
    C_BODY_BLUE = "0D006A"
    C_RED       = "EF4453"
    C_TEAL      = "00B0F0"
    C_LIGHT     = "EDE9FF"
    C_GREY      = "888888"
    C_WHITE     = "FFFFFF"

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── OpenRouter client (same as slides_generator.py) ───────────────────────────

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_para_shading(para, fill_hex: str):
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  fill_hex)
    pPr.append(shd)


def set_para_spacing(para, before: int = 0, after: int = 0):
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(before))
    spacing.set(qn("w:after"),  str(after))
    pPr.insert(0, spacing)


# ── Document building blocks ──────────────────────────────────────────────────

def add_header_bar(doc, tag_text, title, subtitle, tag_color=None, bar_color=None):
    tag_color = tag_color or C_RED
    bar_color = bar_color or C_PURPLE

    tag_p = doc.add_paragraph()
    tag_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    tag_run = tag_p.add_run(tag_text)
    tag_run.bold = True
    tag_run.font.size = Pt(9)
    tag_run.font.color.rgb = rgb(C_WHITE)
    tag_run.font.name = FONT_PRIMARY
    set_para_shading(tag_p, tag_color)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_run = title_p.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(22)
    title_run.font.color.rgb = rgb(C_WHITE)
    title_run.font.name = FONT_PRIMARY
    set_para_shading(title_p, bar_color)
    set_para_spacing(title_p, before=120, after=120)

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(subtitle)
    sub_run.italic = True
    sub_run.font.size = Pt(10)
    sub_run.font.color.rgb = rgb(C_GREY)
    sub_run.font.name = FONT_PRIMARY
    sub_p.paragraph_format.space_after = Pt(16)


def add_section_heading(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = rgb(C_BODY_BLUE)
    run.font.name = FONT_PRIMARY
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), C_TEAL)
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_body_text(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.color.rgb = rgb(C_PURPLE)
    run.font.name = FONT_PRIMARY
    p.paragraph_format.space_after = Pt(8)


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.color.rgb = rgb(C_PURPLE)
    run.font.name = FONT_PRIMARY
    p.paragraph_format.space_after = Pt(4)


def add_highlight_box(doc, label, text):
    p = doc.add_paragraph()
    label_run = p.add_run(f"{label}  ")
    label_run.bold = True
    label_run.font.size = Pt(10)
    label_run.font.color.rgb = rgb(C_BODY_BLUE)
    label_run.font.name = FONT_PRIMARY
    body_run = p.add_run(text)
    body_run.font.size = Pt(10)
    body_run.font.color.rgb = rgb(C_BODY_BLUE)
    body_run.font.name = FONT_PRIMARY
    set_para_shading(p, C_LIGHT)
    p.paragraph_format.left_indent  = Inches(0.2)
    p.paragraph_format.right_indent = Inches(0.2)
    set_para_spacing(p, before=80, after=80)


# ── Pre-bite builder ──────────────────────────────────────────────────────────

def build_pre_bite(data: dict, out_path: str):
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

    add_header_bar(doc, "PRE-BITE",
                   data.get("title", "Session Title"),
                   data.get("subtitle", ""),
                   tag_color=C_RED, bar_color=C_PURPLE)

    if data.get("learning_objectives"):
        add_section_heading(doc, "Learning Objectives")
        for obj in data["learning_objectives"]:
            add_bullet(doc, obj)

    if data.get("context"):
        add_section_heading(doc, "Why This Matters")
        add_body_text(doc, data["context"])

    if data.get("pre_work"):
        add_section_heading(doc, "Before the Session")
        for item in data["pre_work"]:
            add_bullet(doc, item)

    if data.get("reflection_question"):
        doc.add_paragraph()
        add_highlight_box(doc, "Reflect:", data["reflection_question"])

    doc.save(out_path)
    print(f"  ✓ {out_path}")


# ── Post-bite builder ─────────────────────────────────────────────────────────

def build_post_bite(data: dict, out_path: str):
    doc = Document()
    for section in doc.sections:
        section.top_margin    = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

    add_header_bar(doc, "POST-BITE",
                   data.get("title", "Session Title"),
                   data.get("subtitle", ""),
                   tag_color=C_TEAL, bar_color=C_BODY_BLUE)

    if data.get("key_takeaways"):
        add_section_heading(doc, "Key Takeaways")
        for t in data["key_takeaways"]:
            add_bullet(doc, t)

    if data.get("summary"):
        add_section_heading(doc, "Session Summary")
        add_body_text(doc, data["summary"])

    if data.get("next_steps"):
        add_section_heading(doc, "Next Steps")
        for step in data["next_steps"]:
            add_bullet(doc, step)

    if data.get("resources"):
        add_section_heading(doc, "Resources")
        for r in data["resources"]:
            add_bullet(doc, r)

    if data.get("reflection_question"):
        doc.add_paragraph()
        add_highlight_box(doc, "Reflect:", data["reflection_question"])

    doc.save(out_path)
    print(f"  ✓ {out_path}")


# ── LLM content generation ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert instructional designer for Maverx, a Dutch consultancy.
Given a training session intake and slide content, generate structured JSON for
a pre-bite document (sent BEFORE the session) and a post-bite document (sent AFTER).

Return ONLY valid JSON with this exact structure — no markdown, no commentary:
{
  "pre_bite": {
    "title": "...",
    "subtitle": "...",
    "learning_objectives": ["...", "..."],
    "context": "...",
    "pre_work": ["...", "..."],
    "reflection_question": "..."
  },
  "post_bite": {
    "title": "...",
    "subtitle": "...",
    "key_takeaways": ["...", "..."],
    "summary": "...",
    "next_steps": ["...", "..."],
    "resources": ["...", "..."],
    "reflection_question": "..."
  }
}"""


def generate_content(intake: dict, slides: dict) -> dict:
    slide_summary = []
    for slide in slides.get("slides", []):
        title   = slide.get("title", "")
        bullets = slide.get("bullets", slide.get("content", []))
        slide_summary.append(f"- {title}: {'; '.join(str(b) for b in bullets[:3])}")

    user_prompt = f"""Session intake:
{json.dumps(intake, indent=2)}

Slide titles and key points:
{chr(10).join(slide_summary)}

Generate the pre-bite and post-bite JSON now."""

    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```")
        raw = raw.removesuffix("```").strip()

    return json.loads(raw)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)

    intake_path = os.path.join(base_dir, "validated_input.json")
    slides_path = os.path.join(base_dir, "slides_init_text.json")

    if not os.path.exists(intake_path):
        print(f"[ERROR] {intake_path} not found. Run intake agent first.")
        sys.exit(1)
    if not os.path.exists(slides_path):
        print(f"[ERROR] {slides_path} not found. Run slides_generator.py first.")
        sys.exit(1)

    with open(intake_path, encoding="utf-8") as f:
        intake = json.load(f)
    with open(slides_path, encoding="utf-8") as f:
        slides = json.load(f)

    print("[1/3] Generating pre-bite and post-bite content...")
    content = generate_content(intake, slides)
    print("      Content generated.")

    print("[2/3] Building .docx files...")
    build_pre_bite(content["pre_bite"],   os.path.join(base_dir, "pre_bite.docx"))
    build_post_bite(content["post_bite"], os.path.join(base_dir, "post_bite.docx"))

    print("[3/3] Done.")
    print("  ✓ pre_bite.docx")
    print("  ✓ post_bite.docx")