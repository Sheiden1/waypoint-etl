"""Entidade canônica Contact (contato)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contact:
    """Contato associado a um cliente pelo documento do cliente.

    Regra de validação (seção 13): deve ter ao menos ``email`` ou ``phone``.
    """

    customer_document: str
    name: str
    external_id: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None
