"""Catálogo de transformações declaráveis no template De/Para.

Cada nome usado em ``transforms:`` no YAML aponta para uma função aqui. O
catálogo é fechado de propósito: um template não pode executar código
arbitrário, apenas escolher entre transformações auditáveis.

Toda transformação segue o contrato ``str | None -> str | None``. A conversão
para tipos finais (``date``, ``Decimal``) acontece na validação, não aqui — o
mapeamento continua trabalhando com texto.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from ..normalizers import fields, text

Transform = Callable[[str | None], str | None]


def _digits_only(value: str | None) -> str | None:
    """Mantém apenas os dígitos (CPF/CNPJ, telefone, CEP)."""
    return fields.normalize_document(value)


TRANSFORMS: Mapping[str, Transform] = {
    # Texto
    "strip": text.strip,
    "clean_text": text.clean_text,
    "collapse_whitespace": text.collapse_whitespace,
    "remove_control_characters": text.remove_control_characters,
    "normalize_unicode": text.normalize_unicode,
    "remove_accents": text.remove_accents,
    "lowercase": text.lowercase,
    "uppercase": text.uppercase,
    "title_case": text.title_case,
    "nullify_markers": text.nullify_markers,
    # Campos brasileiros
    "digits_only": _digits_only,
    "brazilian_phone": fields.normalize_phone,
    "postal_code": fields.normalize_postal_code,
    "email": fields.normalize_email,
    "uf": fields.normalize_state,
}

# ``brazilian_date`` e ``brazilian_money`` não entram no catálogo: elas mudam o
# tipo do valor e são aplicadas na validação, onde há como reportar o erro de
# conversão como uma issue do registro.
TYPED_TRANSFORM_NAMES: frozenset[str] = frozenset(
    {"brazilian_date", "brazilian_money"}
)


def is_known_transform(name: str) -> bool:
    """Indica se ``name`` existe no catálogo (incluindo as tipadas)."""
    return name in TRANSFORMS or name in TYPED_TRANSFORM_NAMES


def get_transform(name: str) -> Transform:
    """Devolve a transformação pelo nome.

    Levanta ``KeyError`` para nomes desconhecidos; quem carrega o template
    converte isso em uma mensagem acionável antes de chegar ao usuário.
    """
    return TRANSFORMS[name]


def available_transforms() -> tuple[str, ...]:
    """Nomes aceitos em ``transforms:``, em ordem alfabética."""
    return tuple(sorted(set(TRANSFORMS) | TYPED_TRANSFORM_NAMES))


def apply_transforms(value: str | None, names: tuple[str, ...]) -> str | None:
    """Aplica as transformações na ordem declarada.

    As transformações tipadas são ignoradas aqui de propósito: o valor segue
    como texto e a conversão acontece na validação.
    """
    result = value
    for name in names:
        if name in TYPED_TRANSFORM_NAMES:
            continue
        result = TRANSFORMS[name](result)
    return result


__all__ = [
    "TRANSFORMS",
    "TYPED_TRANSFORM_NAMES",
    "Transform",
    "apply_transforms",
    "available_transforms",
    "get_transform",
    "is_known_transform",
]
