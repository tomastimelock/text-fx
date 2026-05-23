# text-fx

120 named text overlay effects for Python video pipelines.

[![PyPI](https://img.shields.io/pypi/v/text-fx)](https://pypi.org/project/text-fx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What it is

text-fx exposes **120 named text overlay effects** through **25 hand-written base engines** with
parametric variants. It was built at Trollfabriken AITrix AB to give programmatic text overlays
the visual vocabulary of consumer video editors — needed for AIMOS Insight municipal report video
subtitles, civic-education explainer captions, and CineForge pipeline trailer titles.

The design follows the same principle as `cut-fx`'s named-transition catalog: consumer editors
expose hundreds of named text effects that are, mechanically, the same handful of base engines
parameterized differently. text-fx publishes that catalog mapping (`effects_catalog.json`,
`effect_mapping.json`) alongside a stable API that `caption-cast` and `title-fx` build on.

The library does not manage subtitle timing, lyric synchronization, or beat-matching — that is
`caption-cast`'s responsibility. text-fx renders one text overlay at a time: text in, animated
transparent WebM out, or text composited directly onto a base video.

---

## What it solves

| Pain point | Resolution |
|---|---|
| Named effects from consumer editors are not reproducible in Python | 120 slugs, each resolved to a deterministic (engine, params) pair from a shipped JSON catalog |
| Every render library has a different text layout API | Single `TextEffectConfig` Pydantic model covers font, position, color, easing, and animation in one place |
| LLM output needs to select text effects by name | `text_effect_schema()` returns a JSON Schema with the full 120-slug enum; `parse_llm_response()` validates and coerces the result |
| Downstream packages need transparent overlay frames, not a re-encoded video | `render_overlay()` returns a transparent WebM with alpha channel; sibling packages composite it without re-rendering the text |

---

## Installation

```bash
pip install text-fx
```

Requires **ffmpeg >= 6.0** on `PATH`. Install it with your OS package manager.

**Extras:**

```bash
pip install "text-fx[overlay]"   # HTML/CSS rendering for light_neon effects (~220 MB)
pip install "text-fx[fonts]"     # system font discovery + variable font support
pip install "text-fx[all]"       # overlay + fonts (~250 MB)
```

The `overlay` extra installs `web-overlay` and Playwright Chromium. On headless servers run
`playwright install chromium` after pip install. See `docs/RUNBOOK.md`.

---

## Quick start

**Apply a named effect to a video:**

```python
from text_fx import apply_text_effect

apply_text_effect(
    video="background.mp4",
    text="HELLO WORLD",
    effect="neon_glow_text",
    output="titled.mp4",
)
```

**Override defaults via `TextEffectConfig`:**

```python
from text_fx import apply_text_effect
from text_fx.config import TextEffectConfig

config = TextEffectConfig(
    text="CHAPTER 1",
    effect="kinetic_pop",
    start_time=1.5,
    duration=2.0,
    font_family="Inter",
    font_size=120,
    color="#FFFFFF",
    easing="ease-out-back",
    intensity=1.2,
    position=("center", "bottom"),
    margin_y=80,
)
apply_text_effect(video="clip.mp4", config=config, output="out.mp4")
```

**Render a transparent overlay (no video input):**

```python
from text_fx import render_overlay

render_overlay(
    text="HELLO",
    effect="neon_glow_text",
    width=1920,
    height=1080,
    duration=2.0,
    fps=30,
    output="hello_neon.webm",
)
# Produces a WebM with alpha channel — composite it onto any video downstream
```

---

## The catalog

120 named effects across 6 categories, each resolved to (base engine, parameter set) via
`effects_catalog.json` and `effect_mapping.json` — both ship inside the wheel.

| Category | Named effects | Base engines | Engines |
|---|---:|---:|---|
| `basic_editing` | 18 | 3 | alpha, typewriter, cascade |
| `kinetic_typography` | 25 | 5 | slide, spring, bounce, spin, oscillate |
| `mask_reveal` | 22 | 4 | linear_wipe, radial, shaped, organic |
| `glitch_digital` | 20 | 4 | rgb_shift, slice_corrupt, decode, scanline |
| `distortion_warp` | 20 | 5 | sine_warp, radial_warp, displacement, motion_blur, particle |
| `light_neon` | 15 | 4 | glow, sweep, shimmer, sparkle |
| **Total** | **120** | **25** | |

Left Wipe, Right Wipe, Top Wipe, Bottom Wipe are four named effects backed by one `linear_wipe`
engine with different `direction` parameters. That pattern — multiple catalog entries, single base
engine — is how the catalog reaches 120 from 25 engines.

**Catalog inspection:**

```python
from text_fx import list_effects, list_categories, get_effect_info

names = list_effects()                          # all 120 slugs
names = list_effects(category="mask_reveal")    # filtered
cats  = list_categories()                       # 6 names

info = get_effect_info("neon_glow_text")
# {
#   "name": "Neon Glow Text", "slug": "neon_glow_text",
#   "categories": ["light_neon"], "base_engine": "glow",
#   "params": {"color": "#FF00FF", "blur_radius": 24, "intensity": 1.5},
#   "duration_default": 2.0
# }
```

---

## Render engines

Engine selection is automatic based on the effect's catalog entry. `prefer_engine` on
`TextEffectConfig` overrides it.

**Pillow (default)** — handles all 25 base engines. Text renders to an RGBA image; the engine
applies per-frame transforms (alpha curves, translations, rotations, mask animations). Frames are
assembled by ffmpeg into a transparent WebM.

**OpenCV** — used automatically for displacement-map effects: `sine_warp`, `radial_warp`,
`displacement`, `motion_blur`, `particle`. OpenCV's `remap` and `filter2D` handle pixel
displacement more efficiently than Pillow for large frames.

**web_overlay (optional)** — some `light_neon` effects (`gold_shine`, `chrome_shine`,
`holographic_text`, `bokeh_text`) and `glitch_digital` effects (`cyberpunk_neon_glitch`,
`hud_text`) look meaningfully better rendered as HTML/CSS animations through Chromium. If
`text-fx[overlay]` is not installed, these effects fall back to a PIL approximation with a
one-time `UserWarning`.

**Render pipeline (three passes):**

1. Typography pass — `typography/renderer.py` renders text to a high-quality RGBA Pillow Image.
2. Animation pass — the engine applies per-frame transformations to produce RGBA frames.
3. Composite pass — `compositor.py` overlays frames onto the base video via ffmpeg
   `filter_complex` with the `overlay` filter. Audio passes through unchanged.

---

## Typography

The library ships no fonts to keep the wheel slim. Resolution order:

1. Explicit path — `font_family="/path/to/Inter-Bold.ttf"` loads that file directly.
2. System fonts — if `text-fx[fonts]` is installed, fonttools discovers the named font on the
   host OS.
3. Fallback — PIL's built-in bitmap font. A warning is logged. The render still proceeds, but
   the output is not suitable for production.

Variable fonts are supported when `fonttools >= 4.43` is installed; `font_weight` maps to the
`wght` axis automatically. Multi-line text uses `\n` in the `text` field.

---

## LLM integration

```python
from text_fx.schema import text_effect_schema, parse_llm_response

schema = text_effect_schema()
# JSON Schema dict; the "effect" field's enum contains all 120 slugs
# Pass as a tool definition or structured-output spec to any LLM

config = parse_llm_response(llm_text)
# Returns a validated TextEffectConfig, or raises pydantic.ValidationError
```

---

## Composition with other Trollfabriken packages

text-fx is the leaf library. `caption-cast` and `title-fx` depend on it; it depends on neither.

`caption-cast` calls `render_overlay()` for each timed caption and composites the resulting
transparent WebMs onto the base video. It adds lyric sync and beat alignment on top.

`title-fx` uses `apply_text_effect()` and `render_overlay()` for its 44 cinematic title recipes,
optionally composing with `cut-fx` for cut-triggered title transitions.

---

## CLI

```bash
# Apply one effect
text-fx apply --video bg.mp4 --text "HELLO" --effect neon_glow_text --out titled.mp4

# Catalog inspection
text-fx list                            # all 120 slugs, one per line
text-fx list --category light_neon      # filtered
text-fx categories                      # 6 category names, one per line
text-fx info neon_glow_text             # JSON metadata

# Engine availability
text-fx engines

# LLM schema
text-fx schema --pretty

# Render transparent overlay (no input video)
text-fx render --text "HELLO" --effect neon_glow_text \
    --width 1920 --height 1080 --duration 2 --out overlay.webm

# Multi-effect sequence from YAML
text-fx sequence --config sequence.yaml --video bg.mp4 --out out.mp4

# Preview over a solid background
text-fx preview --effect neon_glow_text --text "Sample" --out preview.mp4
```

---

## Package structure

```
text-fx/
├── pyproject.toml
├── LICENSE
└── src/text_fx/
    ├── __init__.py          # apply_text_effect, render_overlay, list_effects, …
    ├── api.py
    ├── config.py            # TextEffectConfig
    ├── resolver.py          # slug → (engine, params)
    ├── compositor.py        # ffmpeg overlay compositing
    ├── cli.py
    ├── exceptions.py
    ├── catalog/
    │   ├── loader.py
    │   └── mapping.py
    ├── data/
    │   ├── effects_catalog.json   # ships in wheel
    │   └── effect_mapping.json    # ships in wheel
    ├── typography/
    │   ├── fonts.py         # font loading, system discovery
    │   ├── renderer.py      # PIL text → RGBA
    │   └── layout.py        # multi-line, word/char splitting
    ├── easing/
    │   └── curves.py        # linear, cubic, back, elastic, spring, bounce
    ├── engines/
    │   ├── base.py          # Engine ABC
    │   ├── alpha/           # basic_editing
    │   ├── kinetic/         # kinetic_typography
    │   ├── mask/            # mask_reveal
    │   ├── glitch/          # glitch_digital
    │   ├── distortion/      # distortion_warp
    │   └── neon/            # light_neon
    └── schema/
        ├── generator.py     # text_effect_schema()
        └── parser.py        # parse_llm_response()
```

---

## License

MIT. See [LICENSE](LICENSE).

**Author:** Trollfabriken AITrix AB — https://github.com/tomastimelock

**GitHub:** https://github.com/tomastimelock/text-fx |
**PyPI:** https://pypi.org/project/text-fx/ |
**Issues:** https://github.com/tomastimelock/text-fx/issues

**Sibling packages:** [caption-cast](https://github.com/tomastimelock/caption-cast) —
[title-fx](https://github.com/tomastimelock/title-fx) —
[cut-fx](https://github.com/tomastimelock/cut-fx)
