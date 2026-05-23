"""Test that \\n in text produces multi-line layout."""

from __future__ import annotations

import warnings

from text_fx.typography.layout import compute_layout, split_chars, split_words


def _get_test_font(size: int = 24):
    """Get a font for testing, falling back to PIL default."""
    from text_fx.typography.fonts import load_font

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        return load_font("DejaVu Sans", size=size)


def test_newline_produces_two_lines():
    font = _get_test_font()
    layout = compute_layout("Hello\nWorld", font)
    assert len(layout.lines) == 2
    assert layout.lines[0] == "Hello"
    assert layout.lines[1] == "World"


def test_single_line_has_one_entry():
    font = _get_test_font()
    layout = compute_layout("Hello", font)
    assert len(layout.lines) == 1


def test_three_newlines_produce_four_lines():
    font = _get_test_font()
    layout = compute_layout("A\nB\nC\nD", font)
    assert len(layout.lines) == 4


def test_multiline_total_size_is_positive():
    font = _get_test_font()
    layout = compute_layout("Line one\nLine two", font)
    w, h = layout.total_size
    assert w > 0
    assert h > 0


def test_multiline_height_greater_than_single_line():
    font = _get_test_font()
    single = compute_layout("Hello", font)
    multi = compute_layout("Hello\nWorld", font)
    assert multi.total_size[1] > single.total_size[1]


def test_line_bboxes_count_matches_lines():
    font = _get_test_font()
    layout = compute_layout("A\nB\nC", font)
    assert len(layout.line_bboxes) == len(layout.lines)


def test_word_bboxes_present_for_multiword():
    font = _get_test_font()
    layout = compute_layout("Hello World Foo", font)
    assert len(layout.word_bboxes) == 3


def test_split_words_respects_newlines():
    words = split_words("Hello World\nFoo Bar")
    assert words == ["Hello", "World", "Foo", "Bar"]


def test_split_chars_skips_whitespace():
    chars = split_chars("Hi!")
    assert chars == ["H", "i", "!"]


def test_max_width_triggers_wrapping():
    """With a very small max_width, long text should be split across multiple lines."""
    font = _get_test_font()
    layout_no_wrap = compute_layout("Hello World FooBar Baz", font)
    layout_wrapped = compute_layout("Hello World FooBar Baz", font, max_width=50)
    assert len(layout_wrapped.lines) >= len(layout_no_wrap.lines)
