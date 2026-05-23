"""Test that position keyword strings resolve correctly to pixel offsets."""

from __future__ import annotations

from text_fx.typography.renderer import resolve_position

CANVAS = (640, 360)
TEXT_SIZE = (200, 50)


def test_center_center_is_midpoint():
    px, py = resolve_position(("center", "center"), CANVAS, TEXT_SIZE)
    expected_x = (CANVAS[0] - TEXT_SIZE[0]) // 2
    expected_y = (CANVAS[1] - TEXT_SIZE[1]) // 2
    assert px == expected_x
    assert py == expected_y


def test_left_top_uses_margin():
    margin_x, margin_y = 64, 64
    px, py = resolve_position(
        ("left", "top"), CANVAS, TEXT_SIZE, margin_x=margin_x, margin_y=margin_y
    )
    assert px == margin_x
    assert py == margin_y


def test_right_bottom_uses_margin():
    margin_x, margin_y = 64, 64
    px, py = resolve_position(
        ("right", "bottom"), CANVAS, TEXT_SIZE, margin_x=margin_x, margin_y=margin_y
    )
    assert px == CANVAS[0] - TEXT_SIZE[0] - margin_x
    assert py == CANVAS[1] - TEXT_SIZE[1] - margin_y


def test_integer_position_is_passthrough():
    px, py = resolve_position((100, 200), CANVAS, TEXT_SIZE)
    assert px == 100
    assert py == 200


def test_mixed_keyword_integer():
    px, py = resolve_position(("center", 50), CANVAS, TEXT_SIZE)
    assert px == (CANVAS[0] - TEXT_SIZE[0]) // 2
    assert py == 50


def test_apply_text_effect_with_position_keywords(tiny_video, tmp_path):
    """apply_text_effect should accept keyword position tuples without crashing."""
    from text_fx import apply_text_effect

    positions = [
        ("center", "center"),
        ("left", "top"),
        ("right", "bottom"),
    ]
    for pos in positions:
        out = tmp_path / f"pos_{pos[0]}_{pos[1]}.mp4"
        apply_text_effect(
            video=str(tiny_video),
            text="POSITION TEST",
            effect="fade_in",
            output=str(out),
            duration=1.0,
            position=pos,
        )
        assert out.exists(), f"Output not created for position {pos}"
