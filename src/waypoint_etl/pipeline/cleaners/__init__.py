"""Limpeza de dados (espaços, controle, Unicode)."""

from .patterns import (
    find_cnpjs,
    find_cpfs,
    find_dates,
    find_documents,
    find_emails,
    find_labeled_value,
    find_money_values,
    find_phones,
    find_postal_codes,
)

__all__ = [
    "find_cnpjs",
    "find_cpfs",
    "find_dates",
    "find_documents",
    "find_emails",
    "find_labeled_value",
    "find_money_values",
    "find_phones",
    "find_postal_codes",
]
