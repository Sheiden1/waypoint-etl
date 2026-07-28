"""Testes dos normalizadores de texto."""

from __future__ import annotations

import pytest

from waypoint_etl.pipeline.normalizers.text import (
    clean_text,
    collapse_whitespace,
    lowercase,
    normalize_unicode,
    nullify_markers,
    remove_accents,
    remove_control_characters,
    strip,
    title_case,
    uppercase,
)

# Marcas invisíveis construídas por code point, para não deixar bytes ocultos
# no arquivo de teste.
BOM = chr(0xFEFF)
ZERO_WIDTH_SPACE = chr(0x200B)
COMBINING_ACUTE = chr(0x0301)
COMPOSED = "José"
DECOMPOSED = f"Jose{COMBINING_ACUTE}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("  Ana  ", "Ana"), ("   ", None), ("", None), ("Ana", "Ana")],
)
def test_strip(value: str | None, expected: str | None) -> None:
    assert strip(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("Ana   Silva", "Ana Silva"),
        ("Ana\tSilva", "Ana Silva"),
        ("Ana\nSilva", "Ana Silva"),
        ("  Ana   Maria  Silva  ", "Ana Maria Silva"),
        ("   ", None),
    ],
)
def test_collapse_whitespace(value: str | None, expected: str | None) -> None:
    assert collapse_whitespace(value) == expected


def test_remove_control_characters() -> None:
    assert remove_control_characters("Ana\x00Silva") == "AnaSilva"
    assert remove_control_characters(f"{BOM}Ana") == "Ana"
    assert remove_control_characters(f"A{ZERO_WIDTH_SPACE}na") == "Ana"
    assert remove_control_characters(None) is None


def test_remove_control_characters_keeps_line_breaks() -> None:
    """Quebras e tabulações são tratadas por ``collapse_whitespace``."""
    assert remove_control_characters("Ana\nSilva") == "Ana\nSilva"


def test_normalize_unicode_makes_equal_names_comparable() -> None:
    assert COMPOSED != DECOMPOSED
    assert normalize_unicode(COMPOSED) == normalize_unicode(DECOMPOSED)


def test_remove_accents() -> None:
    assert remove_accents("José Antônio") == "Jose Antonio"
    assert remove_accents("Conceição") == "Conceicao"
    assert remove_accents(None) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("MARIA DA SILVA", "Maria da Silva"),
        ("joão dos santos", "João dos Santos"),
        ("ANA", "Ana"),
        ("comercio de tintas e cores", "Comercio de Tintas e Cores"),
        ("   ", None),
        (None, None),
    ],
)
def test_title_case_preserves_particles(
    value: str | None, expected: str | None
) -> None:
    assert title_case(value) == expected


def test_case_helpers() -> None:
    assert lowercase("ANA") == "ana"
    assert uppercase("ana") == "ANA"
    assert lowercase(None) is None
    assert uppercase(None) is None


@pytest.mark.parametrize(
    "marker", ["-", "--", "N/A", "n/a", "NULL", "nulo", "None", "?", " N/A ", "#N/D"]
)
def test_nullify_markers_recognizes_legacy_placeholders(marker: str) -> None:
    assert nullify_markers(marker) is None


def test_nullify_markers_keeps_real_values() -> None:
    assert nullify_markers("Ana") == "Ana"
    assert nullify_markers("NA Silva") == "NA Silva"
    assert nullify_markers(None) is None


def test_clean_text_combines_the_default_pipeline() -> None:
    assert clean_text("  ANA\x00   SILVA  ") == "ANA SILVA"
    assert clean_text("  N/A  ") is None
    assert clean_text(f"{BOM}  {DECOMPOSED}   Maria ") == "José Maria"
    assert clean_text(None) is None
