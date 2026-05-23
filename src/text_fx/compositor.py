# Filepath: text_fx/compositor.py
# Condensed Description: Composites animated text overlays onto base videos using ffmpeg filter_complex
# Architecture Layer: Library
# Environment: Both
# Script Hierarchy: composite_overlay, build_filter_complex, probe_video
# Dependencies: Internal: config.py, exceptions.py; External: subprocess, pathlib; Providers: None
# Exposes: composite_overlay, build_filter_complex, probe_video
# Configuration: None
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from text_fx.exceptions import CompositorError

logger = logging.getLogger(__name__)


def probe_video(path: Path) -> dict[str, Any]:
    """Use ffprobe to get video metadata.

    Args:
        path: Path to the video file.

    Returns:
        Dict with 'width', 'height', 'fps', 'duration' keys.

    Raises:
        CompositorError: If ffprobe fails or output is unparseable.
    """
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise CompositorError(
            detail=f"ffprobe failed on '{path}'",
            returncode=result.returncode,
            stderr=stderr,
        )

    try:
        data = json.loads(result.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise CompositorError(detail=f"ffprobe output is not valid JSON: {exc}") from exc

    info: dict[str, Any] = {"width": 1920, "height": 1080, "fps": 30.0, "duration": 0.0}

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = int(stream.get("width", 1920))
            info["height"] = int(stream.get("height", 1080))
            # Parse fps from avg_frame_rate "30/1" format
            fps_str = stream.get("avg_frame_rate", "30/1")
            try:
                num, denom = fps_str.split("/")
                info["fps"] = float(num) / max(float(denom), 1)
            except (ValueError, ZeroDivisionError):
                info["fps"] = 30.0
            break

    fmt = data.get("format", {})
    try:
        info["duration"] = float(fmt.get("duration", 0.0))
    except (ValueError, TypeError):
        info["duration"] = 0.0

    return info


def build_filter_complex(start_time: float, end_time: float) -> str:
    """Build the ffmpeg filter_complex string for overlay compositing.

    Args:
        start_time: When the overlay starts in the video (seconds).
        end_time: When the overlay ends (seconds).

    Returns:
        filter_complex string for use with ffmpeg -filter_complex option.
    """
    return (
        f"[1:v]setpts=PTS+{start_time}/TB[ov];"
        f"[0:v][ov]overlay=enable='between(t,{start_time},{end_time})'"
        f":eof_action=pass[outv]"
    )


def composite_overlay(
    base_video: Path,
    overlay: Path,
    start_time: float,
    end_time: float,
    output: Path,
    video_codec: str = "libx264",
    audio_codec: str = "copy",
) -> Path:
    """Overlay a transparent WebM onto a base video at the specified time range.

    Args:
        base_video: Path to the base video file.
        overlay: Path to the WebM overlay file with alpha channel.
        start_time: Start time in seconds.
        end_time: End time in seconds.
        output: Destination path for the composited output.
        video_codec: Output video codec (default 'libx264').
        audio_codec: Output audio codec (default 'copy').

    Returns:
        Path to the composited output file.

    Raises:
        CompositorError: If ffmpeg exits with a non-zero return code.
    """
    filter_complex = build_filter_complex(start_time, end_time)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(base_video),
        "-i",
        str(overlay),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
        "-c:v",
        video_codec,
        "-c:a",
        audio_codec,
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    logger.debug(f"Compositing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True)

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise CompositorError(
            detail="ffmpeg compositing failed",
            returncode=result.returncode,
            stderr=stderr,
        )

    logger.info(f"Composited output written to: {output}")
    return output
