"""Serviços de domínio.

Regras que operam sobre múltiplas entidades ou value objects (ex.: o schema
canônico de destino e as estratégias de deduplicação).
"""

from .canonical_schema import (
    CANONICAL_FIELDS,
    CanonicalField,
    field_names,
    fields_for,
    required_field_names,
)

__all__ = [
    "CANONICAL_FIELDS",
    "CanonicalField",
    "field_names",
    "fields_for",
    "required_field_names",
]
