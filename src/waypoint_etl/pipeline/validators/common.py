"""Validações compartilhadas pelas três entidades canônicas.

Cada função devolve ``(valor convertido, issues)``. Nenhuma levanta exceção: um
registro problemático vira issue e segue para os rejeitados, sem interromper o
lote (seção 17).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ...domain.errors import InvalidDocumentError
from ...domain.value_objects.brazilian_states import is_valid_uf
from ...domain.value_objects.document import Document
from ...domain.value_objects.issue import Issue, error, warning
from ..normalizers.dates import is_future, parse_datetime
from ..normalizers.fields import (
    PHONE_MAX_DIGITS,
    PHONE_MIN_DIGITS,
    is_valid_email,
    is_valid_phone,
    is_valid_postal_code,
)
from ..normalizers.money import parse_decimal

MIN_NAME_LENGTH = 2


def validate_required_text(
    value: str | None, *, field: str, label: str, min_length: int = 1
) -> tuple[str | None, list[Issue]]:
    """Valida um campo textual obrigatório."""
    if value is None:
        return None, [
            error(
                "required_field",
                f"{label} é obrigatório e não foi informado.",
                field=field,
            )
        ]
    if len(value) < min_length:
        return None, [
            error(
                "too_short",
                f"{label} precisa ter ao menos {min_length} caracteres.",
                field=field,
                original_value=value,
            )
        ]
    return value, []


def validate_document(
    value: str | None, *, field: str = "document", label: str = "O documento"
) -> tuple[Document | None, list[Issue]]:
    """Valida CPF/CNPJ pelos dígitos verificadores."""
    if value is None:
        return None, [
            error(
                "required_field",
                f"{label} (CPF/CNPJ) é obrigatório e não foi informado.",
                field=field,
            )
        ]
    try:
        document = Document.parse(value)
    except InvalidDocumentError as exc:
        return None, [
            error(
                "invalid_document",
                f"{label} é inválido: {exc}. Confira o número na origem.",
                field=field,
                original_value=value,
            )
        ]
    return document, []


def validate_optional_email(
    value: str | None, *, field: str = "email"
) -> tuple[str | None, list[Issue]]:
    """Valida o e-mail quando informado; ausência não é problema."""
    if value is None:
        return None, []
    if not is_valid_email(value):
        return None, [
            error(
                "invalid_email",
                "E-mail em formato inválido. Corrija na origem ou remova o valor.",
                field=field,
                original_value=value,
            )
        ]
    return value, []


def validate_optional_phone(
    value: str | None, *, field: str = "phone"
) -> tuple[str | None, list[Issue]]:
    """Valida o telefone normalizado (10 a 13 dígitos)."""
    if value is None:
        return None, []
    if not is_valid_phone(value):
        return None, [
            error(
                "invalid_phone",
                f"Telefone deve ter entre {PHONE_MIN_DIGITS} e "
                f"{PHONE_MAX_DIGITS} dígitos após a normalização.",
                field=field,
                original_value=value,
            )
        ]
    return value, []


def validate_optional_postal_code(
    value: str | None, *, field: str = "postal_code"
) -> tuple[str | None, list[Issue]]:
    """Valida o CEP; um CEP torto alerta, mas não rejeita o cliente."""
    if value is None:
        return None, []
    if not is_valid_postal_code(value):
        return None, [
            warning(
                "invalid_postal_code",
                "CEP não tem oito dígitos e foi descartado.",
                field=field,
                original_value=value,
            )
        ]
    return value, []


def validate_optional_state(
    value: str | None, *, field: str = "state"
) -> tuple[str | None, list[Issue]]:
    """Valida a UF contra o conjunto oficial de siglas."""
    if value is None:
        return None, []
    if not is_valid_uf(value):
        return None, [
            error(
                "invalid_state",
                f"UF '{value}' não é uma sigla válida.",
                field=field,
                original_value=value,
            )
        ]
    return value, []


def validate_date(
    value: str | None,
    *,
    field: str,
    label: str,
    required: bool,
    reject_future: bool = False,
    reference: date | None = None,
) -> tuple[datetime | None, list[Issue]]:
    """Converte e valida uma data brasileira."""
    if value is None:
        if required:
            return None, [
                error(
                    "required_field",
                    f"{label} é obrigatória e não foi informada.",
                    field=field,
                )
            ]
        return None, []

    parsed = parse_datetime(value)
    if parsed is None:
        return None, [
            error(
                "invalid_date",
                f"{label} não está em um formato de data reconhecido "
                "(ex.: 31/12/2024).",
                field=field,
                original_value=value,
            )
        ]

    if reject_future and is_future(parsed, reference=reference):
        return None, [
            error(
                "future_date",
                f"{label} está no futuro.",
                field=field,
                original_value=value,
                normalized_value=parsed.date().isoformat(),
            )
        ]

    return parsed, []


def validate_amount(
    value: str | None, *, field: str = "amount", label: str = "O valor"
) -> tuple[Decimal | None, list[Issue]]:
    """Converte um valor monetário e exige que não seja negativo."""
    if value is None:
        return None, [
            error(
                "required_field",
                f"{label} é obrigatório e não foi informado.",
                field=field,
            )
        ]

    amount = parse_decimal(value)
    if amount is None:
        return None, [
            error(
                "invalid_amount",
                f"{label} não é um número válido (ex.: 1.234,56).",
                field=field,
                original_value=value,
            )
        ]
    if amount < 0:
        return None, [
            error(
                "negative_amount",
                f"{label} não pode ser negativo.",
                field=field,
                original_value=value,
                normalized_value=str(amount),
            )
        ]
    return amount, []


__all__ = [
    "MIN_NAME_LENGTH",
    "validate_amount",
    "validate_date",
    "validate_document",
    "validate_optional_email",
    "validate_optional_phone",
    "validate_optional_postal_code",
    "validate_optional_state",
    "validate_required_text",
]
