# -----------------------------------------------------------------------------
# COLORS
# -----------------------------------------------------------------------------
COLORS = {
    # Primary palette
    "primary_dark":     "#0D006A",   # Titles & body text
    "deep_purple":      "#3F0576",   # Section headers, borders
    "rose_red":         "#EF4453",   # Secondary accent
    "orange":           "#F48A28",   # CTA, inline highlights
    "teal":             "#00B0F0",   # CTA, inline highlights (alt)

    # Tint / light variants (use on dark backgrounds)
    "lavender_tint":    "#BCB3FF",
    "rose_tint":        "#F7B8C0",
    "orange_tint":      "#FAD0A8",
    "teal_tint":        "#9FE6FF",

    # Background colors
    "bg_lavender":      "#EDE9FF",
    "bg_rose":          "#FEF0F1",
    "bg_orange":        "#FDEBDB",
    "bg_teal":          "#E7F9FF",
    "off_white":        "#F2F2F2",   # Default slide background / text on dark

    # Dark backgrounds
    "dark_purple":      "#1A0040",   # Cover & section slides
    "dark_grey":        "#262626",   # Captions, footnotes
}

# Color rules (for LLM design pass)
COLOR_RULES = [
    "Use hard/dark colors (primary_dark, deep_purple, rose_red) for light backgrounds.",
    "Use pastel/tint colors (lavender_tint, rose_tint, teal_tint) for dark backgrounds.",
    "Use no more than three base colors per slide.",
    "New colors must be derived by adding or removing brightness from existing colors — never introduce unrelated colors.",
    "Use orange or teal for CTA elements and inline highlights.",
    "Cover and section divider slides use dark_purple (#1A0040) as background.",
]

# Per-block-type color assignment
BLOCK_COLORS = {
    "cover":       {"bg": "dark_purple",   "title": "off_white",    "accent": "rose_red"},
    "agenda":      {"bg": "off_white",     "title": "primary_dark", "accent": "deep_purple"},
    "kickoff":     {"bg": "bg_lavender",   "title": "primary_dark", "accent": "deep_purple"},
    "theory":      {"bg": "off_white",     "title": "primary_dark", "accent": "teal"},
    "example":     {"bg": "bg_teal",       "title": "primary_dark", "accent": "teal"},
    "exercise":    {"bg": "bg_orange",     "title": "primary_dark", "accent": "orange"},
    "wrapup":      {"bg": "bg_lavender",   "title": "primary_dark", "accent": "deep_purple"},
    "section":     {"bg": "dark_purple",   "title": "off_white",    "accent": "lavender_tint"},
    "timetable":   {"bg": "off_white",     "title": "primary_dark", "accent": "deep_purple"},
    "break":       {"bg": "dark_purple",   "title": "off_white",    "accent": "rose_tint"},
    "debrief":     {"bg": "bg_rose",       "title": "primary_dark", "accent": "rose_red"},
}


# -----------------------------------------------------------------------------
# FONTS
# -----------------------------------------------------------------------------
FONTS = {
    # Primary font — must be downloaded before use (not pre-installed)
    "primary":   "Space Grotesk",
    "secondary": "Raleway",         # Acceptable alternative for body text
    "fallback":  "Calibri",         # Only if Space Grotesk unavailable

    # Sizes (in pt)
    "title":          33,
    "subtitle":       22,
    "sub_subtitle":   21,
    "body":           15,           # Minimum for bullets
    "body_alt":       22,           # Alt style slides — bold bullets
    "body_alt_min":   18,           # Text-heavy slides
    "subtext":        20,           # Indented / secondary text
    "caption":        12,
}

FONT_RULES = [
    "Title font: Space Grotesk Bold, 33pt.",
    "Subtitle: Space Grotesk, 22pt.",
    "Body bullets: Raleway or Space Grotesk, minimum 15pt (18pt acceptable for dense slides).",
    "Alt-style body bullets: 22-24pt Bold.",
    "Do NOT use bullet point symbols (•) for the first line of body text.",
    "Use indentation (tab once) for sub-bullets only.",
    "Emphasize important words with a color accent, not bold or italic alone.",
    "Use empty lines between bullet points or increase line spacing — do not crowd text.",
    "Avoid / and , in slide text where possible; use 'or' and em-dash instead.",
]


# -----------------------------------------------------------------------------
# LAYOUT RULES
# -----------------------------------------------------------------------------
# These map to named slide layouts in the Maverx master .pptx.
# Run this once to verify indices on the actual file:
#   from pptx import Presentation
#   prs = Presentation("maverx_master.pptx")
#   for i, l in enumerate(prs.slide_layouts): print(i, l.name)

LAYOUT_MAP = {
    "cover":        0,   # Dark background, large title, subtitle, logo
    "agenda":       1,   # Two-column agenda list
    "section":      2,   # Section divider — dark bg, large label
    "title_body":   3,   # Standard: title top, bullet body below
    "title_2col":   4,   # Two-column content
    "title_visual": 5,   # Title + image/icon area
    "exercise":     6,   # Exercise layout with numbered steps
    "timetable":    7,   # Time | Module table layout
    "wrapup":       8,   # Wrap-up / key takeaways
    "blank":        9,   # Blank canvas for custom assets
}

# Which layout to assign per didactic block type
BLOCK_LAYOUT = {
    "cover":     "cover",
    "agenda":    "agenda",
    "kickoff":   "title_body",
    "theory":    "title_body",      # Switch to title_2col if >5 bullets
    "example":   "title_visual",    # Prefer visual layout for examples
    "exercise":  "exercise",
    "wrapup":    "wrapup",
    "section":   "section",
    "timetable": "timetable",
    "debrief":   "title_body",
    "break":     "blank",
}


# -----------------------------------------------------------------------------
# MARGINS & SAFE ZONES
# -----------------------------------------------------------------------------
MARGINS = {
    # All values in cm — derived from style guide safe-area diagram
    "safe_top":    2.0,
    "safe_bottom": 1.5,
    "safe_left":   1.5,
    "safe_right":  1.5,
    # No-go zone: outer edges and bottom bar (logo zone)
    "logo_height": 1.2,   # Reserved bar at bottom for maverx.nl / logo
}


# -----------------------------------------------------------------------------
# SLIDE CONTENT RULES
# -----------------------------------------------------------------------------
CONTENT_RULES = {
    "max_bullets_per_slide":     6,
    "max_words_per_bullet":      20,
    "max_title_words":           8,
    "split_threshold_bullets":   6,    # If >6 bullets, split into 2 slides
    "key_takeaway_required_for": ["theory", "example", "wrapup"],
    "key_takeaway_prefix":       "KEY TAKEAWAY —",
}


# -----------------------------------------------------------------------------
# DIDACTIC STRUCTURE
# -----------------------------------------------------------------------------
DIDACTIC_BLOCKS = ["cover", "agenda", "kickoff", "theory", "example", "exercise", "wrapup"]

BLOCK_SLIDE_COUNT = {
    # (min, max) slides per block — scale to training duration
    "cover":     (1, 1),
    "agenda":    (1, 1),
    "kickoff":   (2, 3),
    "theory":    (4, 6),
    "example":   (2, 4),
    "exercise":  (3, 4),   # intro + task description + debrief
    "wrapup":    (2, 3),
}

REQUIRED_SLIDE_TYPES = {
    "cover":      True,
    "agenda":     True,
    "timetable":  True,    # trainer-facing timetable
    "kickoff":    True,
    "wrapup":     True,
}


# -----------------------------------------------------------------------------
# SPEAKER NOTES STRUCTURE
# -----------------------------------------------------------------------------
SPEAKER_NOTE_FIELDS = [
    "aim",                  # One clear sentence on the purpose of this slide
    "time",                 # Short time estimate (e.g. "+/- 5 min")
    "instructions",         # Conversational, trainer-ready step-by-step
    "key_discussion_points",# 3-4 things that must land with participants
    "link_to_reality",      # Concrete story or analogy
    "debrief_summary",      # One punchy closing line
]


# -----------------------------------------------------------------------------
# ASSET TEMPLATES (from style guide slides 42–45)
# -----------------------------------------------------------------------------
ASSET_TEMPLATES = {
    "card_grid":      "Multiple titled cards with short body text + KEY TAKEAWAY bar at bottom",
    "numbered_steps": "Title + subtitle + 1/2/3 numbered items + KEY TAKEAWAY bar",
    "timetable":      "TIME column | MODULE column — rows per block",
    "comparison":     "Two-column card grid for contrasting concepts",
}


# -----------------------------------------------------------------------------
# LOGO & BRANDING
# -----------------------------------------------------------------------------
BRANDING = {
    "logo_path":     "Maverx_Logo.png",   # White version for dark slides
    "website":       "maverx.nl",
    "logo_placement": "bottom-left corner, within logo_height zone",
    "website_placement": "bottom-right, same zone",
}


# --------------------------------------------- --------------------------------
# STYLE GUIDE PROMPT — inject into LLM styling pass
# -----------------------------------------------------------------------------
STYLE_GUIDE_PROMPT = """
You are a visual design assistant for Maverx presentations.
Your job is to enrich a slide JSON with visual design decisions, strictly following the Maverx style guide below.

## Fonts
- Title: Space Grotesk Bold, 33pt
- Subtitle: Space Grotesk, 22pt
- Body bullets: Raleway or Space Grotesk, min 15pt (18pt for dense slides, 22-24pt Bold for alt-style)
- No bullet symbols (•) on first line of body text
- Tab once for sub-bullets
- Emphasize key words with a color accent (not just bold)

## Colors
- primary_dark #0D006A — titles & body
- deep_purple #3F0576 — section headers, borders
- rose_red #EF4453 — secondary accent
- orange #F48A28 — CTA, inline highlights
- teal #00B0F0 — CTA, inline highlights (alt)
- dark_purple #1A0040 — cover & section slide backgrounds
- off_white #F2F2F2 — default slide background
- Use pastel/tint colors on dark backgrounds; use dark/hard colors on light backgrounds
- Max 3 base colors per slide

## Layout decisions
For each slide, output:
- layout_key: one of [cover, agenda, section, title_body, title_2col, title_visual, exercise, timetable, wrapup, blank]
- bg_color: hex from the palette above, matched to block type
- title_color: hex
- accent_color: hex for highlights and key elements
- use_key_takeaway: true/false (required for theory, example, wrapup blocks)
- split_required: true if bullets > 6 (slide must be split by the generator)

## Content rules
- Max 6 bullets per slide; flag split_required if exceeded
- Max 8 words in a title
- KEY TAKEAWAY slides: prefix with "KEY TAKEAWAY —"
- Avoid / and , in text; use em-dash or 'or' instead
- Do not move title position unless absolutely necessary


Return the original JSON structure with these fields added to each slide object:
- layout_key (string)
- bg_color (hex)
- title_color (hex)
- accent_color (hex)
- use_key_takeaway (boolean)
- split_required (boolean)

Do not remove or rename any existing fields.
"""