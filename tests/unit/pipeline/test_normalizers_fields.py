"""Testes dos normalizadores dos campos brasileiros."""

from __future__ import annotations

import pytest

from waypoint_etl.pipeline.normalizers.fields import (
    format_postal_code,
    is_valid_email,
    is_valid_phone,
    is_valid_postal_code,
    normalize_document,
    normalize_email,
    normalize_phone,
    normalize_postal_code,
    normalize_state,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("390.533.447-05", "39053344705"),
        ("39053344705", "39053344705"),
        ("  11.222.333/0001-81  ", "11222333000181"),
        ("N/A", None),
        ("", None),
        (None, None),
        ("sem numero", None),
    ],
)
def test_normalize_document(value: str | None, expected: str | None) -> None:
    assert normalize_document(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("(11) 98765-4321", "11987654321"),
        ("11987654321", "11987654321"),
        ("+55 11 98765-4321", "11987654321"),
        ("5511987654321", "11987654321"),
        ("11 3456-7890", "1134567890"),
        ("-", None),
        (None, None),
    ],
)
def test_normalize_phone(value: str | None, expected: str | None) -> None:
    assert normalize_phone(value) == expected


def test_country_code_is_only_stripped_when_the_rest_looks_national() -> None:
    """Não mutilar um número que legitimamente comece com 55."""
    assert normalize_phone("5551234") == "5551234"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("11987654321", True),
        ("1134567890", True),
        ("5511987654321", True),
        ("123456789", False),
        ("12345678901234", False),
        (None, False),
    ],
)
def test_is_valid_phone(value: str | None, expected: bool) -> None:
    assert is_valid_phone(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("01310-100", "01310100"),
        ("01310100", "01310100"),
        ("1310100", "01310100"),
        ("N/A", None),
        (None, None),
    ],
)
def test_normalize_postal_code(value: str | None, expected: str | None) -> None:
    assert normalize_postal_code(value) == expected


def test_postal_code_recovers_leading_zero_lost_by_spreadsheet() -> None:
    """Planilha converte CEP em número e perde o zero à esquerda."""
    assert normalize_postal_code("1310100") == "01310100"


def test_is_valid_postal_code() -> None:
    assert is_valid_postal_code("01310100")
    assert not is_valid_postal_code("1310100")
    assert not is_valid_postal_code(None)


def test_format_postal_code() -> None:
    assert format_postal_code("01310100") == "01310-100"
    assert format_postal_code("123") == "123"
    assert format_postal_code(None) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  ANA@EXEMPLO.COM.BR ", "ana@exemplo.com.br"),
        ("ana@exemplo.com.br", "ana@exemplo.com.br"),
        ("N/A", None),
        (None, None),
    ],
)
def test_normalize_email(value: str | None, expected: str | None) -> None:
    assert normalize_email(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ana@exemplo.com.br", True),
        ("ana.maria+tag@exemplo.com", True),
        ("sem-arroba.com", False),
        ("usuario@", False),
        ("@dominio.com", False),
        ("ana@dominio", False),
        ("ana silva@dominio.com", False),
        (None, False),
    ],
)
def test_is_valid_email(value: str | None, expected: bool) -> None:
    assert is_valid_email(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("sp", "SP"), ("  rj ", "RJ"), ("N/A", None), (None, None)],
)
def test_normalize_state(value: str | None, expected: str | None) -> None:
    assert normalize_state(value) == expected
