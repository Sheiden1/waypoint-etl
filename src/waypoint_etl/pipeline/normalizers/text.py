"""Normalização de texto: espaços, caracteres de controle, Unicode e nulos.

Todos os normalizadores seguem o mesmo contrato: recebem ``str | None`` e
devolvem ``str | None``. Um valor que "esvazia" durante a limpeza vira ``None``,
nunca string vazia, para que a validação de obrigatoriedade seja uniforme.
"""

from __future__ import annotations

import re
import unicodedata

# Marcadores que sistemas legados usam no lugar de vazio. Comparados sem caixa
# e sem espaços nas pontas.
NULL_MARKERS: frozenset[str] = frozenset(
    {
        "",
        "-",
        "--",
        "---",
        ".",
        "..",
        "n/a",
        "n.a.",
        "na",
        "nd",
        "n/d",
        "null",
        "nulo",
        "none",
        "nenhum",
        "nao informado",
        "não informado",
        "nao informada",
        "não informada",
        "sem informacao",
        "sem informação",
        "vazio",
        "#n/d",
        "#n/a",
        "#valor!",
        "?",
    }
)

# Caracteres de controle e marcas invisíveis (categorias Unicode Cc/Cf), exceto
# quebras de linha e tabulações, que viram espaço em ``collapse_whitespace``.
# Declarados por faixa de code point para não deixar bytes invisíveis no código.
_INVISIBLE_RANGES: tuple[tuple[int, int], ...] = (
    (0x00, 0x08),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x7F, 0x7F),
    (0x200B, 0x200F),  # zero-width space e marcas de direção
    (0x202A, 0x202E),  # sobrescritas de direção bidirecional
    (0xFEFF, 0xFEFF),  # BOM no meio do texto
)
_CONTROL_CHARS = re.compile(
    "[{}]".format(
        "".join(rf"\u{start:04x}-\u{end:04x}" for start, end in _INVISIBLE_RANGES)
    )
)
_WHITESPACE = re.compile(r"\s+")

# Partículas que permanecem em minúsculas no meio de um nome próprio.
_NAME_PARTICLES: frozenset[str] = frozenset(
    {"da", "de", "do", "das", "dos", "e", "di", "du", "van", "von", "del", "la"}
)


def strip(value: str | None) -> str | None:
    """Remove espaços nas pontas; vazio vira ``None``."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def remove_control_characters(value: str | None) -> str | None:
    """Remove caracteres de controle e marcas invisíveis (BOM, zero-width)."""
    if value is None:
        return None
    cleaned = _CONTROL_CHARS.sub("", value)
    return cleaned or None


def collapse_whitespace(value: str | None) -> str | None:
    """Colapsa qualquer sequência de espaços (inclusive quebras) em um espaço."""
    if value is None:
        return None
    collapsed = _WHITESPACE.sub(" ", value).strip()
    return collapsed or None


def normalize_unicode(value: str | None) -> str | None:
    """Aplica a forma canônica NFC.

    Sem isso, "José" com acento combinante e com acento composto seriam tratados
    como nomes diferentes na deduplicação.
    """
    if value is None:
        return None
    return unicodedata.normalize("NFC", value)


def remove_accents(value: str | None) -> str | None:
    """Remove acentos, preservando as letras base.

    Usado apenas em comparações (deduplicação), nunca para gravar o dado.
    """
    if value is None:
        return None
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def lowercase(value: str | None) -> str | None:
    """Converte para minúsculas."""
    return None if value is None else value.lower()


def uppercase(value: str | None) -> str | None:
    """Converte para maiúsculas."""
    return None if value is None else value.upper()


def title_case(value: str | None) -> str | None:
    """Aplica capitalização de nome próprio, preservando partículas.

    "MARIA DA SILVA" vira "Maria da Silva", não "Maria Da Silva".
    """
    if value is None:
        return None
    words = value.lower().split()
    if not words:
        return None

    return " ".join(
        word if index > 0 and word in _NAME_PARTICLES else word.capitalize()
        for index, word in enumerate(words)
    )


def nullify_markers(value: str | None) -> str | None:
    """Converte marcadores de ausência ("N/A", "NULL", "-") em ``None``."""
    if value is None:
        return None
    if value.strip().lower() in NULL_MARKERS:
        return None
    return value


def clean_text(value: str | None) -> str | None:
    """Limpeza padrão aplicada a todo campo textual antes das demais regras.

    A ordem importa: remover controles antes de colapsar espaços, e reconhecer
    marcadores nulos só depois que o valor já está limpo — assim " N/A " também
    é reconhecido.
    """
    value = remove_control_characters(value)
    value = normalize_unicode(value)
    value = collapse_whitespace(value)
    return nullify_markers(value)


__all__ = [
    "NULL_MARKERS",
    "clean_text",
    "collapse_whitespace",
    "lowercase",
    "normalize_unicode",
    "nullify_markers",
    "remove_accents",
    "remove_control_characters",
    "strip",
    "title_case",
    "uppercase",
]
