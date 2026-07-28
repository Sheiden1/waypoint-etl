"""Testes das entidades canônicas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from waypoint_etl.domain.entities import Contact, Customer, Invoice
from waypoint_etl.domain.enums import DocumentType, InvoiceStatus


def test_customer_minimal_fields() -> None:
    customer = Customer(
        full_name="Ana Silva",
        document="11144477735",
        document_type=DocumentType.CPF,
    )
    assert customer.external_id is None
    assert customer.email is None


def test_customer_is_frozen() -> None:
    customer = Customer(
        full_name="Ana Silva",
        document="11144477735",
        document_type=DocumentType.CPF,
    )
    with pytest.raises(AttributeError):
        customer.full_name = "Outro"  # type: ignore[misc]


def test_contact_optional_contacts() -> None:
    contact = Contact(customer_document="11144477735", name="João")
    assert contact.email is None
    assert contact.phone is None


def test_invoice_uses_decimal_amount() -> None:
    invoice = Invoice(
        external_id="NF-1",
        customer_document="11144477735",
        issued_at=date(2024, 1, 10),
        due_at=date(2024, 2, 10),
        amount=Decimal("1234.56"),
        status=InvoiceStatus.OPEN,
    )
    assert isinstance(invoice.amount, Decimal)
    assert invoice.status is InvoiceStatus.OPEN
