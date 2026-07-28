"""Entidade canônica Customer (cliente)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..enums.document_type import DocumentType


@dataclass(frozen=True, slots=True)
class Customer:
    """Cliente no schema canônico de destino.

    Campos obrigatórios: ``full_name``, ``document`` e ``document_type``. O
    ``document`` é armazenado somente com dígitos (normalizado).
    """

    full_name: str
    document: str
    document_type: DocumentType
    external_id: str | None = None
    email: str | None = None
    phone: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    created_at: datetime | None = None
