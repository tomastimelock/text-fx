# Filepath: text_fx/cli.py
# Condensed Description: CLI entry point using argparse; subcommands apply, list, categories, info, engines, schema, render, sequence, preview
# Architecture Layer: CLI
# Environment: Both
# Script Hierarchy: main, cmd_apply, cmd_list, cmd_categories, cmd_info, cmd_engines, cmd_schema, cmd_render, cmd_sequence, cmd_preview
# Dependencies: Internal: api.py, catalog/loader.py, catalog/mapping.py, engines/__init__.py, schema/generator.py, config.py, exceptions.py; External: argparse, json, sys; Providers: None
# Exposes: main
# Configuration: None
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Build the root argument parser with all subcommands.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="text-fx",
        description="text-fx: 120 named text overlay effects for video.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command", required=True)

    # apply
    p_apply = sub.add_parser("apply", help="Apply a text effect to a video file")
    p_apply.add_argument("--video", required=True, help="Input video path")
    p_apply.add_argument("--text", required=True, help="Text to render")
    p_apply.add_argument("--effect", required=True, help="Effect slug")
    p_apply.add_argument("--out", required=True, help="Output video path")
    p_apply.add_argument("--duration", type=float, default=2.0, help="Effect duration in seconds")
    p_apply.add_argument("--start", type=float, default=0.0, help="Start time in video (seconds)")
    p_apply.add_argument("--font", default="Inter", help="Font family name or .ttf path")
    p_apply.add_argument("--font-size", type=int, default=96, help="Font size in pixels")
    p_apply.add_argument("--color", default="#FFFFFF", help="Text color (CSS hex)")
    p_apply.add_argument("--stroke-color", default=None, help="Stroke color")
    p_apply.add_argument("--stroke-width", type=int, default=0, help="Stroke width pixels")

    # list
    p_list = sub.add_parser("list", help="List all effect slugs")
    p_list.add_argument("--category", default=None, help="Filter by category")

    # categories
    sub.add_parser("categories", help="List all categories")

    # info
    p_info = sub.add_parser("info", help="Get metadata for an effect")
    p_info.add_argument("effect", help="Effect slug or name")
    p_info.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")

    # engines
    sub.add_parser("engines", help="List available engines and their availability")

    # schema
    p_schema = sub.add_parser("schema", help="Print JSON schema for LLM use")
    p_schema.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    # render
    p_render = sub.add_parser("render", help="Render a text effect to a transparent WebM overlay")
    p_render.add_argument("--text", required=True, help="Text to render")
    p_render.add_argument("--effect", required=True, help="Effect slug")
    p_render.add_argument("--out", required=True, help="Output .webm path")
    p_render.add_argument("--width", type=int, default=1920, help="Canvas width")
    p_render.add_argument("--height", type=int, default=1080, help="Canvas height")
    p_render.add_argument("--duration", type=float, default=2.0, help="Duration in seconds")
    p_render.add_argument("--fps", type=int, default=30, help="Frame rate")

    # sequence
    p_seq = sub.add_parser("sequence", help="Apply a sequence of effects from a YAML/JSON config")
    p_seq.add_argument("--config", required=True, help="Path to YAML or JSON sequence config")
    p_seq.add_argument("--video", required=True, help="Input video path")
    p_seq.add_argument("--out", required=True, help="Output video path")

    # preview
    p_prev = sub.add_parser("preview", help="Preview an effect over a solid-color background")
    p_prev.add_argument("--effect", required=True, help="Effect slug")
    p_prev.add_argument("--text", default="Sample", help="Preview text")
    p_prev.add_argument("--out", default="preview.mp4", help="Output path")
    p_prev.add_argument("--width", type=int, default=1920)
    p_prev.add_argument("--height", type=int, default=1080)
    p_prev.add_argument("--duration", type=float, default=3.0)
    p_prev.add_argument("--bg-color", default="#1a1a2e", help="Background color (CSS hex)")

    return parser


def cmd_apply(args: argparse.Namespace) -> int:
    """Handle the 'apply' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code (0 = success).
    """
    from text_fx.api import apply_text_effect

    kwargs: dict[str, Any] = {
        "font_family": args.font,
        "font_size": args.font_size,
        "color": args.color,
    }
    if args.stroke_color:
        kwargs["stroke_color"] = args.stroke_color
        kwargs["stroke_width"] = args.stroke_width

    try:
        result = apply_text_effect(
            video=args.video,
            text=args.text,
            effect=args.effect,
            output=args.out,
            duration=args.duration,
            start_time=args.start,
            **kwargs,
        )
        print(f"Output written to: {result}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the 'list' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.api import list_effects

    try:
        effects = list_effects(category=args.category)
        for slug in effects:
            print(slug)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_categories(args: argparse.Namespace) -> int:
    """Handle the 'categories' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.api import list_categories

    try:
        cats = list_categories()
        for cat in cats:
            print(cat)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the 'info' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.api import get_effect_info

    try:
        info = get_effect_info(args.effect)
        print(json.dumps(info, indent=2))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_engines(args: argparse.Namespace) -> int:
    """Handle the 'engines' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.engines import ENGINE_REGISTRY

    for name, engine in sorted(ENGINE_REGISTRY.items()):
        available = engine.is_available()
        status = "available" if available else "unavailable"
        print(f"{name:20s}  {status:12s}  {engine.__class__.__name__}")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Handle the 'schema' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.schema import schema_json

    try:
        print(schema_json(pretty=args.pretty))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_render(args: argparse.Namespace) -> int:
    """Handle the 'render' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.api import render_overlay

    try:
        result = render_overlay(
            text=args.text,
            effect=args.effect,
            width=args.width,
            height=args.height,
            duration=args.duration,
            fps=args.fps,
            output=args.out,
        )
        print(f"Overlay written to: {result}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_sequence(args: argparse.Namespace) -> int:
    """Handle the 'sequence' subcommand.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    from text_fx.api import apply_text_sequence

    config_path = Path(args.config)
    try:
        if config_path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml

                with open(config_path, encoding="utf-8") as f:
                    effects = yaml.safe_load(f)
            except ImportError:
                print(
                    "PyYAML is required for YAML sequence configs: pip install pyyaml",
                    file=sys.stderr,
                )
                return 1
        else:
            with open(config_path, encoding="utf-8") as f:
                effects = json.load(f)

        result = apply_text_sequence(video=args.video, effects=effects, output=args.out)
        print(f"Output written to: {result}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_preview(args: argparse.Namespace) -> int:
    """Handle the 'preview' subcommand.

    Creates a solid-colour background video and applies the effect to it.

    Args:
        args: Parsed argument namespace.

    Returns:
        Exit code.
    """
    import subprocess
    import tempfile

    from text_fx.api import apply_text_effect

    try:
        # Create background video with ffmpeg
        with tempfile.TemporaryDirectory() as tmpdir:
            bg_path = Path(tmpdir) / "bg.mp4"
            bg_color = args.bg_color.lstrip("#")
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=0x{bg_color}:size={args.width}x{args.height}:rate=30:duration={args.duration}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(bg_path),
            ]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                print(f"Failed to create background: {result.stderr.decode()}", file=sys.stderr)
                return 1

            out = apply_text_effect(
                video=bg_path,
                text=args.text,
                effect=args.effect,
                output=args.out,
                duration=args.duration,
            )
            print(f"Preview written to: {out}")
            return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


_COMMAND_HANDLERS = {
    "apply": cmd_apply,
    "list": cmd_list,
    "categories": cmd_categories,
    "info": cmd_info,
    "engines": cmd_engines,
    "schema": cmd_schema,
    "render": cmd_render,
    "sequence": cmd_sequence,
    "preview": cmd_preview,
}


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list; defaults to sys.argv.

    Returns:
        Exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    handler = _COMMAND_HANDLERS.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 2

    return handler(args)
