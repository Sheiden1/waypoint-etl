"""Descrição dos campos canônicos de destino por entidade.

Fica no domínio porque é a definição do schema para o qual toda migração
converge — o template De/Para e os validadores consultam a mesma fonte, em vez
de repetirem listas de campos que sairiam de sincronia.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..enums.entity_type import EntityType


@dataclass(frozen=True, slots=True)
class CanonicalField:
    """Um campo do schema de destino."""

    name: str
    required: bool
    description: str


_CUSTOMER_FIELDS: tuple[CanonicalField, ...] = (
    CanonicalField("external_id", False, "Identificador no sistema de origem"),
    CanonicalField("full_name", True, "Nome completo ou razão social"),
    CanonicalField("document", True, "CPF ou CNPJ (somente dígitos)"),
    CanonicalField("email", False, "E-mail principal"),
    CanonicalField("phone", False, "Telefone principal"),
    CanonicalField("postal_code", False, "CEP"),
    CanonicalField("city", False, "Cidade"),
    CanonicalField("state", False, "UF"),
    CanonicalField("created_at", False, "Data de cadastro na origem"),
)

_CONTACT_FIELDS: tuple[CanonicalField, ...] = (
    CanonicalField("external_id", False, "Identificador no sistema de origem"),
    CanonicalField("customer_document", True, "CPF/CNPJ do cliente vinculado"),
    CanonicalField("name", True, "Nome do contato"),
    CanonicalField("role", False, "Cargo ou função"),
    CanonicalField("email", False, "E-mail do contato"),
    CanonicalField("phone", False, "Telefone do contato"),
)

_INVOICE_FIELDS: tuple[CanonicalField, ...] = (
    CanonicalField("external_id", True, "Identificador da cobrança na origem"),
    CanonicalField("customer_document", True, "CPF/CNPJ do cliente"),
    CanonicalField("description", False, "Descrição da cobrança"),
    CanonicalField("issued_at", True, "Data de emissão"),
    CanonicalField("due_at", True, "Data de vencimento"),
    CanonicalField("amount", True, "Valor"),
    CanonicalField("status", True, "Status da cobrança"),
)

CANONICAL_FIELDS: dict[EntityType, tuple[CanonicalField, ...]] = {
    EntityType.CUSTOMERS: _CUSTOMER_FIELDS,
    EntityType.CONTACTS: _CONTACT_FIELDS,
    EntityType.INVOICES: _INVOICE_FIELDS,
}


def fields_for(entity: EntityType) -> tuple[CanonicalField, ...]:
    """Devolve os campos canônicos da entidade."""
    return CANONICAL_FIELDS[entity]


def field_names(entity: EntityType) -> tuple[str, ...]:
    """Nomes de todos os campos canônicos da entidade."""
    return tuple(field.name for field in fields_for(entity))


def required_field_names(entity: EntityType) -> tuple[str, ...]:
    """Nomes dos campos obrigatórios da entidade."""
    return tuple(field.name for field in fields_for(entity) if field.required)


__all__ = [
    "CANONICAL_FIELDS",
    "CanonicalField",
    "field_names",
    "fields_for",
    "required_field_names",
]
