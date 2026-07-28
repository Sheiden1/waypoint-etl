"""Repositórios de persistência."""

from .entities import (
    add_entities,
    to_contact_model,
    to_customer_model,
    to_invoice_model,
    to_issue_model,
)

__all__ = [
    "add_entities",
    "to_contact_model",
    "to_customer_model",
    "to_invoice_model",
    "to_issue_model",
]
