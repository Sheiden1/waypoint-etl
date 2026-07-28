"""Conversão das entidades canônicas para os modelos persistidos."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from ...domain.entities.contact import Contact
from ...domain.entities.customer import Customer
from ...domain.entities.invoice import Invoice
from ...domain.enums.entity_type import EntityType
from ...domain.value_objects.issue import Issue
from ..database.models import (
    ContactModel,
    CustomerModel,
    InvoiceModel,
    MigrationIssueModel,
)


def to_customer_model(entity: Customer, run_id: uuid.UUID) -> CustomerModel:
    """Converte um ``Customer`` canônico no modelo persistido."""
    return CustomerModel(
        run_id=run_id,
        external_id=entity.external_id,
        full_name=entity.full_name,
        document=entity.document,
        document_type=entity.document_type.value,
        email=entity.email,
        phone=entity.phone,
        postal_code=entity.postal_code,
        city=entity.city,
        state=entity.state,
        created_at=entity.created_at,
    )


def to_contact_model(entity: Contact, run_id: uuid.UUID) -> ContactModel:
    """Converte um ``Contact`` canônico no modelo persistido."""
    return ContactModel(
        run_id=run_id,
        external_id=entity.external_id,
        customer_document=entity.customer_document,
        name=entity.name,
        role=entity.role,
        email=entity.email,
        phone=entity.phone,
    )


def to_invoice_model(entity: Invoice, run_id: uuid.UUID) -> InvoiceModel:
    """Converte um ``Invoice`` canônico no modelo persistido."""
    return InvoiceModel(
        run_id=run_id,
        external_id=entity.external_id,
        customer_document=entity.customer_document,
        description=entity.description,
        issued_at=entity.issued_at,
        due_at=entity.due_at,
        amount=entity.amount,
        status=entity.status.value,
    )


def to_issue_model(
    issue: Issue, run_id: uuid.UUID, row_number: int | None
) -> MigrationIssueModel:
    """Converte uma ``Issue`` no modelo persistido.

    Espera a issue já mascarada (``Issue.for_display()``): documentos completos
    não devem ser gravados nas tabelas de auditoria (seção 18).
    """
    return MigrationIssueModel(
        run_id=run_id,
        row_number=row_number,
        code=issue.code,
        severity=issue.severity.value,
        field=issue.field,
        message=issue.message,
        original_value=issue.original_value,
        normalized_value=issue.normalized_value,
    )


def add_entities(
    session: Session,
    entities: Sequence[Customer | Contact | Invoice],
    entity_type: EntityType,
    run_id: uuid.UUID,
) -> int:
    """Adiciona as entidades à sessão e devolve quantas foram enfileiradas.

    Não faz commit: a transação é controlada por quem chama, para que a carga
    inteira seja atômica.
    """
    models: list[CustomerModel | ContactModel | InvoiceModel] = []
    for entity in entities:
        if isinstance(entity, Customer) and entity_type is EntityType.CUSTOMERS:
            models.append(to_customer_model(entity, run_id))
        elif isinstance(entity, Contact) and entity_type is EntityType.CONTACTS:
            models.append(to_contact_model(entity, run_id))
        elif isinstance(entity, Invoice) and entity_type is EntityType.INVOICES:
            models.append(to_invoice_model(entity, run_id))
        else:
            raise TypeError(
                f"Entidade {type(entity).__name__} não corresponde ao tipo de "
                f"migração '{entity_type.value}'."
            )

    session.add_all(models)
    return len(models)


__all__ = [
    "add_entities",
    "to_contact_model",
    "to_customer_model",
    "to_invoice_model",
    "to_issue_model",
]
