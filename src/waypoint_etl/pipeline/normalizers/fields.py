"""Normalizadores dos campos brasileiros do schema canônico.

Normalizar é diferente de validar: aqui o valor ganha forma canônica (só
dígitos, minúsculas, sem máscara). Se ele é *aceitável* é decisão dos
validadores (Dia 6).
"""

from __future__ import annotations

import re

from ...domain.value_objects.document import only_digits
from .text import clean_text, lowercase

# Telefone brasileiro após normalização: 10 ou 11 dígitos (DDD + número), ou
# 12/13 com o código do país.
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 13
COUNTRY_CODE = "55"

POSTAL_CODE_LENGTH = 8

# Verificação estrutural de e-mail: um @, parte local e domínio com ponto.
# Regex reconhece o padrão; a validade real só o envio comprovaria.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


def normalize_email(value: str | None) -> str | None:
    """Limpa e converte o e-mail para minúsculas."""
    return lowercase(clean_text(value))


def is_valid_email(value: str | None) -> bool:
    """Indica se o texto tem estrutura de e-mail."""
    if value is None:
        return False
    return _EMAIL.match(value.strip()) is not None


def normalize_document(value: str | None) -> str | None:
    """Reduz CPF/CNPJ a somente dígitos, removendo qualquer máscara."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    digits = only_digits(cleaned)
    return digits or None


def normalize_phone(value: str | None) -> str | None:
    """Reduz o telefone a somente dígitos, sem o código do país.

    ``+55 (11) 98765-4321`` vira ``11987654321``. O código 55 só é removido
    quando o que sobra tem tamanho de telefone nacional, para não mutilar um
    número que legitimamente comece com 55.
    """
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    digits = only_digits(cleaned)
    if not digits:
        return None

    if digits.startswith(COUNTRY_CODE):
        without_country = digits[len(COUNTRY_CODE) :]
        if len(without_country) in (10, 11):
            return without_country

    return digits


def is_valid_phone(value: str | None) -> bool:
    """Indica se o telefone normalizado tem entre 10 e 13 dígitos (seção 13)."""
    if value is None:
        return False
    digits = only_digits(value)
    return PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS


def normalize_postal_code(value: str | None) -> str | None:
    """Reduz o CEP a somente dígitos.

    CEPs exportados de planilha costumam perder o zero à esquerda ao virarem
    número; sete dígitos são completados à esquerda.
    """
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    digits = only_digits(cleaned)
    if not digits:
        return None
    if len(digits) == POSTAL_CODE_LENGTH - 1:
        digits = digits.zfill(POSTAL_CODE_LENGTH)
    return digits


def is_valid_postal_code(value: str | None) -> bool:
    """Indica se o CEP normalizado tem exatamente oito dígitos."""
    if value is None:
        return False
    return len(only_digits(value)) == POSTAL_CODE_LENGTH


def format_postal_code(value: str | None) -> str | None:
    """Formata o CEP como ``00000-000`` para exibição."""
    if value is None:
        return None
    digits = only_digits(value)
    if len(digits) != POSTAL_CODE_LENGTH:
        return digits or None
    return f"{digits[:5]}-{digits[5:]}"


def normalize_state(value: str | None) -> str | None:
    """Reduz a UF a duas letras maiúsculas."""
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    return cleaned.upper()


__all__ = [
    "COUNTRY_CODE",
    "PHONE_MAX_DIGITS",
    "PHONE_MIN_DIGITS",
    "POSTAL_CODE_LENGTH",
    "format_postal_code",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_postal_code",
    "normalize_document",
    "normalize_email",
    "normalize_phone",
    "normalize_postal_code",
    "normalize_state",
]
