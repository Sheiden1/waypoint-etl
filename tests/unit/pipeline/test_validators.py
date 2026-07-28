"""Testes das validações, severidades e separação de rejeitados."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from waypoint_etl.domain.entities.contact import Contact
from waypoint_etl.domain.entities.customer import Customer
from waypoint_etl.domain.entities.invoice import Invoice
from waypoint_etl.domain.enums.document_type import DocumentType
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.enums.invoice_status import InvoiceStatus
from waypoint_etl.pipeline.mappers.mapper import MappedRecord
from waypoint_etl.pipeline.validators import validate_record, validate_records

VALID_CPF = "39053344705"
VALID_CNPJ = "11222333000181"
REFERENCE = date(2024, 6, 1)

CUSTOMER = {
    "full_name": "Ana Silva",
    "document": VALID_CPF,
    "email": "ana@exemplo.com.br",
    "phone": "11987654321",
    "postal_code": "01310100",
    "city": "São Paulo",
    "state": "SP",
    "created_at": "15/03/2024",
    "external_id": "ERP-1",
}

CONTACT = {
    "customer_document": VALID_CPF,
    "name": "Bruno Souza",
    "email": "bruno@exemplo.com.br",
    "phone": None,
    "role": "Comprador",
    "external_id": None,
}

INVOICE = {
    "external_id": "NF-1",
    "customer_document": VALID_CNPJ,
    "issued_at": "01/03/2024",
    "due_at": "31/03/2024",
    "amount": "1.234,56",
    "status": "aberto",
    "description": "Servicos",
}


def _validate(values: dict[str, str | None], entity: EntityType):  # type: ignore[no-untyped-def]
    return validate_record(
        MappedRecord(row_number=2, values=values), entity, reference_date=REFERENCE
    )


def _codes(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {issue.code for issue in result.issues}


# --- Customer ----------------------------------------------------------------


def test_valid_customer_becomes_entity() -> None:
    result = _validate(dict(CUSTOMER), EntityType.CUSTOMERS)

    assert result.is_valid
    assert result.issues == ()
    assert isinstance(result.entity, Customer)
    assert result.entity.document == VALID_CPF
    assert result.entity.document_type is DocumentType.CPF
    assert result.entity.created_at is not None


def test_customer_without_name_is_rejected() -> None:
    result = _validate({**CUSTOMER, "full_name": None}, EntityType.CUSTOMERS)

    assert not result.is_valid
    assert result.entity is None
    assert "required_field" in _codes(result)


def test_customer_with_one_letter_name_is_rejected() -> None:
    result = _validate({**CUSTOMER, "full_name": "A"}, EntityType.CUSTOMERS)

    assert "too_short" in _codes(result)


def test_customer_with_invalid_check_digits_is_rejected() -> None:
    result = _validate({**CUSTOMER, "document": "11111111111"}, EntityType.CUSTOMERS)

    assert not result.is_valid
    assert "invalid_document" in _codes(result)


def test_customer_with_invalid_email_is_rejected() -> None:
    result = _validate({**CUSTOMER, "email": "sem-arroba.com"}, EntityType.CUSTOMERS)

    assert "invalid_email" in _codes(result)


def test_customer_with_short_phone_is_rejected() -> None:
    result = _validate({**CUSTOMER, "phone": "12345"}, EntityType.CUSTOMERS)

    assert "invalid_phone" in _codes(result)


def test_customer_with_unknown_uf_is_rejected() -> None:
    result = _validate({**CUSTOMER, "state": "XX"}, EntityType.CUSTOMERS)

    assert "invalid_state" in _codes(result)


def test_future_registration_date_is_rejected() -> None:
    result = _validate({**CUSTOMER, "created_at": "01/01/2030"}, EntityType.CUSTOMERS)

    assert "future_date" in _codes(result)


def test_bad_postal_code_only_warns() -> None:
    """CEP torto não deve impedir a migração do cliente."""
    result = _validate({**CUSTOMER, "postal_code": "123"}, EntityType.CUSTOMERS)

    assert result.is_valid
    assert result.entity is not None
    assert result.entity.postal_code is None
    assert "invalid_postal_code" in {issue.code for issue in result.warnings}


def test_optional_fields_may_be_absent() -> None:
    minimal = {"full_name": "Ana Silva", "document": VALID_CPF}

    result = _validate(minimal, EntityType.CUSTOMERS)

    assert result.is_valid
    assert result.entity is not None
    assert result.entity.email is None


def test_all_problems_are_reported_at_once() -> None:
    """O usuário deve corrigir tudo de uma vez, não um erro por rodada."""
    result = _validate(
        {"full_name": None, "document": "111", "email": "x", "state": "ZZ"},
        EntityType.CUSTOMERS,
    )

    assert {"required_field", "invalid_document", "invalid_email", "invalid_state"} <= (
        _codes(result)
    )


# --- Contact -----------------------------------------------------------------


def test_valid_contact_becomes_entity() -> None:
    result = _validate(dict(CONTACT), EntityType.CONTACTS)

    assert result.is_valid
    assert isinstance(result.entity, Contact)


def test_contact_without_email_and_phone_is_rejected() -> None:
    result = _validate(
        {**CONTACT, "email": None, "phone": None}, EntityType.CONTACTS
    )

    assert not result.is_valid
    assert "missing_contact_channel" in _codes(result)


def test_contact_with_only_phone_is_accepted() -> None:
    result = _validate(
        {**CONTACT, "email": None, "phone": "11987654321"}, EntityType.CONTACTS
    )

    assert result.is_valid


def test_contact_requires_customer_document() -> None:
    result = _validate({**CONTACT, "customer_document": None}, EntityType.CONTACTS)

    assert "required_field" in _codes(result)


# --- Invoice -----------------------------------------------------------------


def test_valid_invoice_becomes_entity() -> None:
    result = _validate(dict(INVOICE), EntityType.INVOICES)

    assert result.is_valid
    assert isinstance(result.entity, Invoice)
    assert result.entity.amount == Decimal("1234.56")
    assert result.entity.status is InvoiceStatus.OPEN
    assert result.entity.issued_at == date(2024, 3, 1)


def test_invoice_amount_uses_decimal_not_float() -> None:
    result = _validate({**INVOICE, "amount": "0,10"}, EntityType.INVOICES)

    assert result.entity is not None
    assert isinstance(result.entity.amount, Decimal)
    assert result.entity.amount == Decimal("0.10")


def test_zero_amount_is_accepted() -> None:
    result = _validate({**INVOICE, "amount": "0,00"}, EntityType.INVOICES)

    assert result.is_valid


def test_negative_amount_is_rejected() -> None:
    result = _validate({**INVOICE, "amount": "-10,00"}, EntityType.INVOICES)

    assert "negative_amount" in _codes(result)


def test_due_before_issue_is_rejected() -> None:
    result = _validate(
        {**INVOICE, "issued_at": "31/03/2024", "due_at": "01/03/2024"},
        EntityType.INVOICES,
    )

    assert "due_before_issue" in _codes(result)


def test_unknown_status_is_rejected() -> None:
    result = _validate({**INVOICE, "status": "estranho"}, EntityType.INVOICES)

    assert "unknown_status" in _codes(result)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pago", InvoiceStatus.PAID),
        ("vencido", InvoiceStatus.OVERDUE),
        ("cancelado", InvoiceStatus.CANCELED),
        ("open", InvoiceStatus.OPEN),
    ],
)
def test_status_is_converted_to_the_canonical_enum(
    raw: str, expected: InvoiceStatus
) -> None:
    result = _validate({**INVOICE, "status": raw}, EntityType.INVOICES)

    assert result.entity is not None
    assert result.entity.status is expected


def test_invoice_requires_external_id() -> None:
    result = _validate({**INVOICE, "external_id": None}, EntityType.INVOICES)

    assert "required_field" in _codes(result)


# --- Lote --------------------------------------------------------------------


def test_one_bad_record_does_not_stop_the_batch() -> None:
    records = (
        MappedRecord(2, dict(CUSTOMER)),
        MappedRecord(3, {**CUSTOMER, "document": "111"}),
        MappedRecord(4, dict(CUSTOMER)),
    )

    results = validate_records(
        records, EntityType.CUSTOMERS, reference_date=REFERENCE
    )

    assert [r.is_valid for r in results] == [True, False, True]
    assert [r.row_number for r in results] == [2, 3, 4]


def test_rejected_record_keeps_original_values_for_the_report() -> None:
    result = _validate({**CUSTOMER, "document": "111"}, EntityType.CUSTOMERS)

    assert result.values["document"] == "111"
    assert result.values["full_name"] == "Ana Silva"


def test_document_is_masked_for_display() -> None:
    """Seção 18: CPF/CNPJ completos não podem aparecer na auditoria."""
    result = _validate({**CUSTOMER, "document": "11111111111"}, EntityType.CUSTOMERS)

    displayed = [
        issue for issue in result.issues_for_display() if issue.field == "document"
    ]

    assert displayed
    assert displayed[0].original_value == "111.***.***-11"
