"""Testes dos enums canônicos."""

from __future__ import annotations

import pytest

from waypoint_etl.domain.enums import (
    DocumentType,
    EntityType,
    InvoiceStatus,
    IssueSeverity,
)


def test_enums_are_str_based() -> None:
    assert DocumentType.CPF == "cpf"
    assert EntityType.CUSTOMERS == "customers"
    assert IssueSeverity.ERROR == "error"
    assert str(InvoiceStatus.PAID) == "paid"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("aberto", InvoiceStatus.OPEN),
        ("Pago", InvoiceStatus.PAID),
        ("  VENCIDO ", InvoiceStatus.OVERDUE),
        ("cancelled", InvoiceStatus.CANCELED),
    ],
)
def test_invoice_status_from_raw(raw: str, expected: InvoiceStatus) -> None:
    assert InvoiceStatus.from_raw(raw) is expected


def test_invoice_status_from_raw_unknown_raises() -> None:
    with pytest.raises(ValueError, match="desconhecido"):
        InvoiceStatus.from_raw("estado-invalido")
