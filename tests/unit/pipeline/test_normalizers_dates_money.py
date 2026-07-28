"""Testes de conversão de datas brasileiras e de moeda."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from waypoint_etl.pipeline.normalizers.dates import (
    is_future,
    parse_date,
    parse_datetime,
)
from waypoint_etl.pipeline.normalizers.money import parse_decimal


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("15/03/2024", date(2024, 3, 15)),
        ("15-03-2024", date(2024, 3, 15)),
        ("15.03.2024", date(2024, 3, 15)),
        ("2024-03-15", date(2024, 3, 15)),
        ("2024/03/15", date(2024, 3, 15)),
        ("15032024", date(2024, 3, 15)),
        ("15/03/24", date(2024, 3, 15)),
        ("  15/03/2024  ", date(2024, 3, 15)),
    ],
)
def test_parse_date_accepts_legacy_formats(value: str, expected: date) -> None:
    assert parse_date(value) == expected


def test_day_comes_before_month() -> None:
    """``03/04/2024`` é 3 de abril: convenção brasileira, nunca americana."""
    assert parse_date("03/04/2024") == date(2024, 4, 3)


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "não informado", "31/02/2024", "15/13/2024", "abc", "2024"],
)
def test_parse_date_returns_none_instead_of_guessing(value: str | None) -> None:
    """Dado ausente é recuperável; dado errado, não."""
    assert parse_date(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("15/03/2024 08:30", datetime(2024, 3, 15, 8, 30)),
        ("15/03/2024 08:30:45", datetime(2024, 3, 15, 8, 30, 45)),
        ("2024-03-15 08:30:45", datetime(2024, 3, 15, 8, 30, 45)),
        ("2024-03-15T08:30:45", datetime(2024, 3, 15, 8, 30, 45)),
        ("15/03/2024", datetime(2024, 3, 15, 0, 0)),
    ],
)
def test_parse_datetime(value: str, expected: datetime) -> None:
    assert parse_datetime(value) == expected


def test_is_future_uses_injected_reference() -> None:
    reference = date(2024, 3, 15)

    assert is_future(date(2024, 3, 16), reference=reference)
    assert not is_future(date(2024, 3, 15), reference=reference)
    assert not is_future(date(2024, 3, 14), reference=reference)
    assert is_future(datetime(2024, 3, 16, 10, 0), reference=reference)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("R$ 1.234,56", Decimal("1234.56")),
        ("R$1.234,56", Decimal("1234.56")),
        ("1.234,56", Decimal("1234.56")),
        ("1234,56", Decimal("1234.56")),
        ("1234.56", Decimal("1234.56")),
        ("1234", Decimal("1234")),
        ("0,00", Decimal("0.00")),
        ("1.234.567,89", Decimal("1234567.89")),
        ("  R$ 99,90  ", Decimal("99.90")),
        ("BRL 10,00", Decimal("10.00")),
    ],
)
def test_parse_decimal_accepts_brazilian_currency(
    value: str, expected: Decimal
) -> None:
    assert parse_decimal(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("-1.234,56", Decimal("-1234.56")),
        ("(1.234,56)", Decimal("-1234.56")),
        ("1.234,56-", Decimal("-1234.56")),
    ],
)
def test_parse_decimal_handles_negatives(value: str, expected: Decimal) -> None:
    assert parse_decimal(value) == expected


def test_parse_decimal_keeps_precision_without_float() -> None:
    """Somar centavos em ``float`` acumularia erro; ``Decimal`` não."""
    total = sum(
        (parse_decimal("0,10") or Decimal(0) for _ in range(10)), start=Decimal(0)
    )

    assert total == Decimal("1.00")


def test_american_notation_is_recognized() -> None:
    assert parse_decimal("1,234.56") == Decimal("1234.56")


@pytest.mark.parametrize(
    "value", [None, "", "   ", "N/A", "abc", "R$", "1,2,3", "12/03/2024"]
)
def test_parse_decimal_returns_none_for_non_numbers(value: str | None) -> None:
    assert parse_decimal(value) is None
