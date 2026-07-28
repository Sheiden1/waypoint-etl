"""Testes dos utilitários compartilhados pelos extratores."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from waypoint_etl.infrastructure.extractors.base import (
    build_row_mapping,
    coerce_cell,
    is_blank_row,
    normalize_headers,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("  Ana  ", "Ana"),
        (True, "true"),
        (False, "false"),
        (1000, "1000"),
        (1000.0, "1000"),
        (1234.5, "1234.5"),
        (Decimal("10.50"), "10.50"),
        (dt.date(2024, 3, 15), "2024-03-15"),
        (dt.datetime(2024, 3, 15), "2024-03-15"),
        (dt.datetime(2024, 3, 15, 8, 30), "2024-03-15 08:30:00"),
        (dt.time(8, 30), "08:30:00"),
    ],
)
def test_coerce_cell(value: object, expected: str | None) -> None:
    assert coerce_cell(value) == expected


def test_coerce_cell_falls_back_to_string() -> None:
    class Opaque:
        def __str__(self) -> str:
            return "  valor  "

    assert coerce_cell(Opaque()) == "valor"


def test_normalize_headers_collapses_internal_whitespace() -> None:
    columns, warnings = normalize_headers(["  Nome   Cliente  "])

    assert columns == ("Nome Cliente",)
    assert warnings == ()


def test_normalize_headers_handles_three_repeated_names() -> None:
    columns, warnings = normalize_headers(["fone", "fone", "fone"])

    assert columns == ("fone", "fone (2)", "fone (3)")
    assert len(warnings) == 2


def test_is_blank_row() -> None:
    assert is_blank_row([None, None])
    assert not is_blank_row([None, "x"])


def test_build_row_mapping_pads_and_truncates() -> None:
    assert build_row_mapping(["a", "b"], ["1"]) == {"a": "1", "b": None}
    assert build_row_mapping(["a"], ["1", "2"]) == {"a": "1"}
