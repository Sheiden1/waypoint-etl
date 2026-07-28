"""Tipos de entidade suportados pela migração."""

from __future__ import annotations

from enum import StrEnum


class EntityType(StrEnum):
    """Entidades canônicas migradas pelo Waypoint."""

    CUSTOMERS = "customers"
    CONTACTS = "contacts"
    INVOICES = "invoices"
