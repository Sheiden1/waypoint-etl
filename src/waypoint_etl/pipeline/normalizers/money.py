"""Conversão de moeda brasileira para ``Decimal``.

Valores monetários nunca usam ``float`` (seção 9): a soma de centavos em ponto
flutuante acumula erro e uma migração financeira não pode fechar com diferença.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Símbolos e sufixos que acompanham o valor em exportações legadas.
_CURRENCY_NOISE = re.compile(r"(?i)(r\$|brl|\s)")
_ALLOWED = re.compile(r"^-?[\d.,]+$")
_TRAILING_MINUS = re.compile(r"^([\d.,]+)-$")
# Formato brasileiro: ponto separa milhar, vírgula separa decimal.
_BRAZILIAN = re.compile(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$|^-?\d+(,\d+)?$")


def parse_decimal(value: str | None) -> Decimal | None:
    """Converte texto monetário em ``Decimal``; ``None`` quando não for número.

    Aceita ``R$ 1.234,56``, ``1234,56``, ``1234.56``, negativos com sinal à
    esquerda ou à direita e valores entre parênteses (convenção contábil).
    """
    if value is None:
        return None

    text = value.strip()
    if not text:
        return None

    text, negative_by_parentheses = _strip_accounting_parentheses(text)
    text = _CURRENCY_NOISE.sub("", text)
    if not text:
        return None

    text, negative_by_suffix = _strip_trailing_minus(text)
    if not _ALLOWED.match(text):
        return None

    normalized = _to_decimal_text(text)
    if normalized is None:
        return None

    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None

    if negative_by_parentheses or negative_by_suffix:
        amount = -abs(amount)
    return amount


def _strip_accounting_parentheses(text: str) -> tuple[str, bool]:
    """``(1.234,56)`` representa valor negativo na convenção contábil."""
    if text.startswith("(") and text.endswith(")"):
        return text[1:-1].strip(), True
    return text, False


def _strip_trailing_minus(text: str) -> tuple[str, bool]:
    """Alguns ERPs exportam o sinal negativo depois do número (``1234,56-``)."""
    match = _TRAILING_MINUS.match(text)
    if match is not None:
        return match.group(1), True
    return text, False


def _to_decimal_text(text: str) -> str | None:
    """Converte a notação brasileira ou americana para o formato do ``Decimal``.

    A ambiguidade real é ``1.234``: milhar no Brasil, decimal nos EUA. Como o
    projeto trata dados brasileiros, o formato brasileiro tem precedência.
    """
    if _BRAZILIAN.match(text):
        return text.replace(".", "").replace(",", ".")

    # Notação americana: vírgula como milhar (1,234.56).
    if text.count(",") >= 1 and text.rfind(".") > text.rfind(","):
        return text.replace(",", "")

    # Só pontos e mais de um: são separadores de milhar (1.234.567).
    if text.count(".") > 1:
        return text.replace(".", "")

    if text.count(",") > 1:
        return None

    return text.replace(",", ".")


__all__ = ["parse_decimal"]
