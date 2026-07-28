"""Validação dos registros mapeados para as entidades canônicas (seção 13)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from ...domain.entities.contact import Contact
from ...domain.entities.customer import Customer
from ...domain.entities.invoice import Invoice
from ...domain.enums.entity_type import EntityType
from ...domain.enums.invoice_status import InvoiceStatus
from ...domain.value_objects.issue import Issue, error
from ..mappers.mapper import MappedRecord
from .common import (
    MIN_NAME_LENGTH,
    validate_amount,
    validate_date,
    validate_document,
    validate_optional_email,
    validate_optional_phone,
    validate_optional_postal_code,
    validate_optional_state,
    validate_required_text,
)
from .result import ValidatedRecord


def validate_record(
    record: MappedRecord,
    entity_type: EntityType,
    *,
    reference_date: date | None = None,
) -> ValidatedRecord:
    """Valida um registro mapeado de acordo com a entidade de destino."""
    validators = {
        EntityType.CUSTOMERS: _validate_customer,
        EntityType.CONTACTS: _validate_contact,
        EntityType.INVOICES: _validate_invoice,
    }
    entity, issues = validators[entity_type](record.values, reference_date)

    return ValidatedRecord(
        row_number=record.row_number,
        entity_type=entity_type,
        values=record.values,
        issues=tuple(issues),
        entity=entity if not any(issue.is_error for issue in issues) else None,
        sheet=record.sheet,
    )


def validate_records(
    records: tuple[MappedRecord, ...],
    entity_type: EntityType,
    *,
    reference_date: date | None = None,
) -> tuple[ValidatedRecord, ...]:
    """Valida um lote inteiro. Um registro problemático não afeta os demais."""
    return tuple(
        validate_record(record, entity_type, reference_date=reference_date)
        for record in records
    )


def _validate_customer(
    values: Mapping[str, str | None], reference_date: date | None
) -> tuple[Customer | None, list[Issue]]:
    """Regras de Customer (seção 13)."""
    issues: list[Issue] = []

    name, name_issues = validate_required_text(
        values.get("full_name"),
        field="full_name",
        label="O nome",
        min_length=MIN_NAME_LENGTH,
    )
    issues += name_issues

    document, document_issues = validate_document(values.get("document"))
    issues += document_issues

    email, email_issues = validate_optional_email(values.get("email"))
    issues += email_issues

    phone, phone_issues = validate_optional_phone(values.get("phone"))
    issues += phone_issues

    postal_code, postal_issues = validate_optional_postal_code(
        values.get("postal_code")
    )
    issues += postal_issues

    state, state_issues = validate_optional_state(values.get("state"))
    issues += state_issues

    created_at, date_issues = validate_date(
        values.get("created_at"),
        field="created_at",
        label="A data de cadastro",
        required=False,
        reject_future=True,
        reference=reference_date,
    )
    issues += date_issues

    if name is None or document is None:
        return None, issues

    return (
        Customer(
            full_name=name,
            document=document.value,
            document_type=document.type,
            external_id=values.get("external_id"),
            email=email,
            phone=phone,
            postal_code=postal_code,
            city=values.get("city"),
            state=state,
            created_at=created_at,
        ),
        issues,
    )


def _validate_contact(
    values: Mapping[str, str | None], reference_date: date | None
) -> tuple[Contact | None, list[Issue]]:
    """Regras de Contact (seção 13)."""
    issues: list[Issue] = []

    document, document_issues = validate_document(
        values.get("customer_document"),
        field="customer_document",
        label="O documento do cliente",
    )
    issues += document_issues

    name, name_issues = validate_required_text(
        values.get("name"),
        field="name",
        label="O nome do contato",
        min_length=MIN_NAME_LENGTH,
    )
    issues += name_issues

    email, email_issues = validate_optional_email(values.get("email"))
    issues += email_issues

    phone, phone_issues = validate_optional_phone(values.get("phone"))
    issues += phone_issues

    # Um contato sem nenhuma forma de contato não serve ao destino.
    if email is None and phone is None:
        issues.append(
            error(
                "missing_contact_channel",
                "O contato precisa ter ao menos e-mail ou telefone.",
                field="email",
            )
        )

    if document is None or name is None:
        return None, issues

    return (
        Contact(
            customer_document=document.value,
            name=name,
            external_id=values.get("external_id"),
            role=values.get("role"),
            email=email,
            phone=phone,
        ),
        issues,
    )


def _validate_invoice(
    values: Mapping[str, str | None], reference_date: date | None
) -> tuple[Invoice | None, list[Issue]]:
    """Regras de Invoice (seção 13)."""
    issues: list[Issue] = []

    external_id, external_issues = validate_required_text(
        values.get("external_id"),
        field="external_id",
        label="O identificador da cobrança",
    )
    issues += external_issues

    document, document_issues = validate_document(
        values.get("customer_document"),
        field="customer_document",
        label="O documento do cliente",
    )
    issues += document_issues

    issued_at, issued_issues = validate_date(
        values.get("issued_at"),
        field="issued_at",
        label="A data de emissão",
        required=True,
    )
    issues += issued_issues

    due_at, due_issues = validate_date(
        values.get("due_at"),
        field="due_at",
        label="A data de vencimento",
        required=True,
    )
    issues += due_issues

    amount, amount_issues = validate_amount(values.get("amount"))
    issues += amount_issues

    status, status_issues = _validate_status(values.get("status"))
    issues += status_issues

    if issued_at is not None and due_at is not None and due_at < issued_at:
        issues.append(
            error(
                "due_before_issue",
                "O vencimento é anterior à emissão.",
                field="due_at",
                original_value=values.get("due_at"),
            )
        )

    if (
        external_id is None
        or document is None
        or issued_at is None
        or due_at is None
        or amount is None
        or status is None
    ):
        return None, issues

    return (
        Invoice(
            external_id=external_id,
            customer_document=document.value,
            issued_at=issued_at.date(),
            due_at=due_at.date(),
            amount=amount,
            status=status,
            description=values.get("description"),
        ),
        issues,
    )


def _validate_status(value: str | None) -> tuple[InvoiceStatus | None, list[Issue]]:
    """Converte o status de origem para o enum canônico."""
    if value is None:
        return None, [
            error(
                "required_field",
                "O status da cobrança é obrigatório e não foi informado.",
                field="status",
            )
        ]
    try:
        return InvoiceStatus.from_raw(value), []
    except ValueError:
        return None, [
            error(
                "unknown_status",
                f"Status '{value}' não corresponde a nenhum status canônico "
                "(aberto, pago, vencido ou cancelado).",
                field="status",
                original_value=value,
            )
        ]


__all__ = ["validate_record", "validate_records"]
