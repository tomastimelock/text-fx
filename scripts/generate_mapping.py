# Filepath: scripts/generate_mapping.py
# Condensed Description: Dev-time script; classifies all 120 catalog slugs into engine mappings and writes effect_mapping.json
# Architecture Layer: Utility
# Environment: Local
# Script Hierarchy: main, build_mapping
# Dependencies: Internal: None (reads catalog JSON directly); External: stdlib json, pathlib; Providers: None
# Exposes: Nothing (run as script)
# Configuration: None
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Maps primary category to default engine bucket
CATEGORY_TO_ENGINE_BUCKET: dict[str, str] = {
    "basic_editing": "alpha",
    "kinetic_typography": "kinetic",
    "mask_reveal": "mask",
    "glitch_digital": "glitch",
    "distortion_warp": "distortion",
    "light_neon": "neon",
}

# Maps category to default base engine within that bucket
CATEGORY_TO_BASE_ENGINE: dict[str, str] = {
    "basic_editing": "fade",
    "kinetic_typography": "slide",
    "mask_reveal": "linear_wipe",
    "glitch_digital": "slice_corrupt",
    "distortion_warp": "sine_warp",
    "light_neon": "glow",
}

# Explicit per-slug overrides: slug → (base_engine, params)
NAME_TO_BASE: dict[str, tuple[str, dict[str, Any]]] = {
    # basic_editing
    "fade_in": ("fade", {"direction": "in"}),
    "fade_out": ("fade", {"direction": "out"}),
    "cross_dissolve_text": ("fade", {"direction": "cross"}),
    "hard_cut_title": ("fade", {"direction": "hard"}),
    "dip_to_black_title": ("fade", {"direction": "dip_black"}),
    "dip_to_white_title": ("fade", {"direction": "dip_white"}),
    "blur_fade_in": ("fade", {"direction": "in", "blur": True}),
    "blur_fade_out": ("fade", {"direction": "out", "blur": True}),
    "typewriter": ("typewriter", {"show_cursor": False}),
    "cursor_typewriter": ("typewriter", {"show_cursor": True}),
    "backspace_delete": ("typewriter", {"reverse": True}),
    "word_reveal": ("cascade", {"unit": "word"}),
    "line_reveal": ("cascade", {"unit": "line"}),
    "character_fade_cascade": ("cascade", {"unit": "char"}),
    "word_fade_cascade": ("cascade", {"unit": "word", "fade": True}),
    # kinetic_typography
    "kinetic_pop": ("bounce", {"scale_start": 0.8, "scale_overshoot": 1.1}),
    "bounce_text": ("bounce", {}),
    "elastic_text": ("spring", {"frequency": 12.0, "damping": 2.0}),
    "punch_zoom_title": ("bounce", {"scale_start": 3.0, "motion_blur": True}),
    "impact_slam": ("slide", {"direction": "down", "shake": True, "impact_frames": 5}),
    "drop_in": ("slide", {"direction": "down"}),
    "rise_up": ("slide", {"direction": "up", "fade": True}),
    "slide_left_text": ("slide", {"direction": "left"}),
    "slide_right_text": ("slide", {"direction": "right"}),
    "slide_up_text": ("slide", {"direction": "up"}),
    "slide_down_text": ("slide", {"direction": "down"}),
    "overshoot_slide": ("slide", {"direction": "left", "overshoot": True}),
    "spring_words": ("spring", {"per_word": True}),
    "scale_cascade": ("oscillate", {"mode": "scale_cascade"}),
    "wave_text": ("oscillate", {"mode": "wave"}),
    "jitter_text": ("oscillate", {"mode": "jitter"}),
    "shake_text": ("oscillate", {"mode": "shake"}),
    "wiggle_text": ("oscillate", {"mode": "wiggle"}),
    "spin_in": ("spin", {"direction": "in"}),
    "spin_out": ("spin", {"direction": "out"}),
    "flip_x": ("spin", {"axis": "x"}),
    "flip_y": ("spin", {"axis": "y"}),
    "3d_rotate_title": ("spin", {"axis": "perspective"}),
    "orbit_text": ("oscillate", {"mode": "orbit"}),
    "circular_text_motion": ("oscillate", {"mode": "circular"}),
    # mask_reveal
    "linear_wipe_reveal": ("linear_wipe", {"direction": "left_to_right"}),
    "left_wipe": ("linear_wipe", {"direction": "left_to_right"}),
    "right_wipe": ("linear_wipe", {"direction": "right_to_left"}),
    "top_wipe": ("linear_wipe", {"direction": "top_to_bottom"}),
    "bottom_wipe": ("linear_wipe", {"direction": "bottom_to_top"}),
    "split_reveal": ("linear_wipe", {"direction": "split"}),
    "center_slice_reveal": ("linear_wipe", {"direction": "center_out"}),
    "circle_reveal": ("radial", {"mode": "circle"}),
    "radial_reveal": ("radial", {"mode": "wedge"}),
    "diagonal_wipe": ("linear_wipe", {"direction": "diagonal"}),
    "venetian_blinds": ("shaped", {"shape": "venetian", "count": 10}),
    "vertical_blinds": ("shaped", {"shape": "vertical_blinds", "count": 10}),
    "shutter_reveal": ("shaped", {"shape": "shutter", "count": 6}),
    "box_reveal": ("shaped", {"shape": "box"}),
    "frame_reveal": ("shaped", {"shape": "frame"}),
    "ink_matte_reveal": ("organic", {"mode": "ink"}),
    "smoke_matte_reveal": ("organic", {"mode": "smoke"}),
    "paint_brush_reveal": ("organic", {"mode": "brush"}),
    "scratch_reveal": ("organic", {"mode": "scratch"}),
    "glitch_mask_reveal": ("shaped", {"shape": "glitch_slices", "count": 12}),
    # glitch_digital
    "rgb_split_text": ("rgb_shift", {"offset": 10}),
    "chromatic_aberration": ("rgb_shift", {"offset": 3}),
    "digital_glitch_title": ("slice_corrupt", {"mode": "slices", "slice_count": 15}),
    "data_moshing_text": ("slice_corrupt", {"mode": "datamosh"}),
    "pixel_sort_text": ("slice_corrupt", {"mode": "pixel_sort"}),
    "scanline_text": ("scanline", {"mode": "scanline"}),
    "crt_flicker": ("scanline", {"mode": "flicker"}),
    "vhs_title": ("scanline", {"mode": "vhs"}),
    "bad_signal": ("scanline", {"mode": "bad_signal"}),
    "terminal_text": ("decode", {"mode": "terminal"}),
    "matrix_rain_behind_text": ("decode", {"mode": "matrix", "background_rain": True}),
    "hacker_decode": ("decode", {"mode": "hacker"}),
    "binary_decode": ("decode", {"mode": "binary", "charset": "binary"}),
    "hud_text": ("scanline", {"mode": "hud", "hud_lines": True}),
    "cyberpunk_neon_glitch": ("rgb_shift", {"offset": 8, "glow": True}),
    "pixelated_reveal": ("scanline", {"mode": "pixelate"}),
    "block_corruption": ("slice_corrupt", {"mode": "blocks"}),
    "glitch_flash": ("slice_corrupt", {"mode": "flash"}),
    "static_noise_fill": ("slice_corrupt", {"mode": "static"}),
    "digital_tear": ("slice_corrupt", {"mode": "tear"}),
    # distortion_warp
    "wave_distortion": ("sine_warp", {"mode": "wave", "amplitude_y": 15.0, "frequency": 2.0}),
    "heat_haze_text": ("sine_warp", {"mode": "heat", "amplitude_y": 8.0}),
    "liquid_ripple": ("radial_warp", {"mode": "ripple", "strength": 0.5}),
    "magnify_text": ("radial_warp", {"mode": "magnify", "strength": 0.6}),
    "bulge_text": ("radial_warp", {"mode": "bulge", "strength": 0.5}),
    "pinch_text": ("radial_warp", {"mode": "pinch", "strength": 0.5}),
    "twirl_text": ("radial_warp", {"mode": "twirl", "strength": 0.6}),
    "stretch_text": ("displacement", {"mode": "stretch"}),
    "smear_text": ("displacement", {"mode": "smear"}),
    "echo_trails": ("sine_warp", {"mode": "echo", "echo_count": 4}),
    "motion_blur_text": ("motion_blur", {"mode": "directional", "kernel_length": 30}),
    "zoom_blur_text": ("motion_blur", {"mode": "zoom", "kernel_length": 20}),
    "broken_glass_text": ("displacement", {"mode": "shatter", "shard_count": 16}),
    "paper_tear_text": ("displacement", {"mode": "tear", "shard_count": 8}),
    "pixel_melt": ("motion_blur", {"mode": "melt"}),
    "sand_dissolve": ("particle", {"mode": "sand"}),
    "particle_disperse": ("particle", {"mode": "disperse"}),
    "ash_disintegration": ("particle", {"mode": "ash"}),
    "fragment_explosion": ("particle", {"mode": "explode"}),
    "magnetic_assemble": ("particle", {"mode": "assemble"}),
    # light_neon
    "neon_glow_text": (
        "glow",
        {"color": "#FF00FF", "blur_radius": 24, "intensity": 1.5, "mode": "glow"},
    ),
    "neon_flicker": (
        "glow",
        {"color": "#FF00FF", "blur_radius": 20, "flicker": True, "mode": "glow"},
    ),
    "light_sweep": ("sweep", {"mode": "linear_sweep"}),
    "glow_pulse": ("glow", {"color": "#00FFFF", "blur_radius": 20, "pulse": True, "mode": "pulse"}),
    "aura_text": ("glow", {"color": "#8800FF", "blur_radius": 32, "mode": "aura"}),
    "laser_scan_text": ("sweep", {"mode": "laser"}),
    "hologram_text": ("shimmer", {"mode": "hologram"}),
    "projected_light_text": ("shimmer", {"mode": "projected"}),
    "spotlight_text": ("sweep", {"mode": "spotlight"}),
    "shadow_cast_title": ("glow", {"color": "#000000", "blur_radius": 16, "mode": "shadow"}),
    "gold_shine": ("shimmer", {"mode": "gold"}),
    "chrome_shine": ("shimmer", {"mode": "chrome"}),
    "fire_glow": ("glow", {"color": "#FF6600", "blur_radius": 28, "mode": "fire"}),
    "electric_outline": ("sparkle", {"mode": "electric"}),
    "lightning_text": ("sparkle", {"mode": "lightning"}),
    "strobe_title": ("sweep", {"mode": "strobe", "strobe_hz": 6.0}),
    "flash_frame_title": ("sweep", {"mode": "flash"}),
    "lens_dust_sparkle": ("sparkle", {"mode": "dust", "count": 30}),
    "star_sparkle_text": ("sparkle", {"mode": "star", "count": 20, "star_points": 4}),
    "bokeh_text": ("shimmer", {"mode": "bokeh", "bokeh_count": 25}),
}

# Prefer-engine overrides (slugs where web_overlay is preferred for best quality)
PREFER_ENGINE_OVERRIDES: dict[str, str] = {
    "gold_shine": "web_overlay",
    "chrome_shine": "web_overlay",
    "hologram_text": "web_overlay",
    "bokeh_text": "web_overlay",
    "cyberpunk_neon_glitch": "web_overlay",
    "hud_text": "web_overlay",
}


def build_mapping(catalog_path: Path) -> list[dict[str, Any]]:
    """Build the complete effect mapping from the catalog.

    Args:
        catalog_path: Path to the effects_catalog.json file.

    Returns:
        List of mapping entry dicts, one per effect slug.
    """
    with open(catalog_path, encoding="utf-8") as f:
        catalog_data = json.load(f)

    entries = []
    for transition in catalog_data.get("transitions", []):
        slug = transition.get("slug")
        if not slug:
            continue
        categories = transition.get("categories", [])
        primary_category = categories[0] if categories else "basic_editing"

        if slug in NAME_TO_BASE:
            base_engine, params = NAME_TO_BASE[slug]
        else:
            base_engine = CATEGORY_TO_BASE_ENGINE.get(primary_category, "fade")
            params = {}
            logger.warning(
                f"No explicit mapping for slug '{slug}'; using category default '{base_engine}'"
            )

        engine_bucket = CATEGORY_TO_ENGINE_BUCKET.get(primary_category, "alpha")
        prefer_engine = PREFER_ENGINE_OVERRIDES.get(slug, "auto")

        entries.append(
            {
                "slug": slug,
                "base_engine": base_engine,
                "engine_bucket": engine_bucket,
                "params": params,
                "prefer_engine": prefer_engine,
            }
        )

    return entries


def main() -> None:
    """Main entry point for the mapping generator script."""
    repo_root = Path(__file__).parent.parent
    catalog_path = repo_root / "src" / "text_fx" / "data" / "effects_catalog.json"
    output_path = repo_root / "src" / "text_fx" / "data" / "effect_mapping.json"

    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found at {catalog_path}")

    logger.info(f"Reading catalog from {catalog_path}")
    entries = build_mapping(catalog_path)
    logger.info(f"Generated {len(entries)} mapping entries")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote effect_mapping.json to {output_path}")


if __name__ == "__main__":
    main()
