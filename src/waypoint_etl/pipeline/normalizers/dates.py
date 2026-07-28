"""Conversão segura de datas brasileiras.

"Segura" significa: nunca adivinhar. ``03/04/2024`` é sempre 3 de abril (padrão
brasileiro), e formatos ambíguos ou impossíveis devolvem ``None`` em vez de uma
data errada — um dado ausente é recuperável, um dado errado não.
"""

from __future__ import annotations

import re
from datetime import date, datetime

# Formatos aceitos, na ordem de tentativa. O dia vem antes do mês em todos os
# formatos com separador, seguindo a convenção brasileira.
DATE_FORMATS: tuple[str, ...] = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%y",
    "%d-%m-%y",
)

DATETIME_FORMATS: tuple[str, ...] = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
)

# ``ddmmaaaa`` sem separador, comum em exportações de sistemas antigos.
_COMPACT_DATE = re.compile(r"^(\d{2})(\d{2})(\d{4})$")


def parse_date(value: str | None) -> date | None:
    """Converte texto em ``date``; devolve ``None`` quando não for uma data."""
    parsed = parse_datetime(value)
    return parsed.date() if parsed is not None else None


def parse_datetime(value: str | None) -> datetime | None:
    """Converte texto em ``datetime``; devolve ``None`` quando não for uma data.

    Datas sem hora recebem meia-noite. Valores fora do calendário (31/02) são
    rejeitados pelo próprio ``strptime``.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None

    for fmt in DATETIME_FORMATS:
        parsed = _try_format(text, fmt)
        if parsed is not None:
            return parsed

    for fmt in DATE_FORMATS:
        parsed = _try_format(text, fmt)
        if parsed is not None:
            return parsed

    return _parse_compact(text)


def _try_format(text: str, fmt: str) -> datetime | None:
    """Tenta um formato específico, sem propagar o erro."""
    try:
        return datetime.strptime(text, fmt)
    except ValueError:
        return None


def _parse_compact(text: str) -> datetime | None:
    """Interpreta ``ddmmaaaa`` (oito dígitos, sem separador)."""
    match = _COMPACT_DATE.match(text)
    if match is None:
        return None
    day, month, year = match.groups()
    return _try_format(f"{day}/{month}/{year}", "%d/%m/%Y")


def is_future(value: date | datetime, *, reference: date | None = None) -> bool:
    """Indica se a data é posterior à referência (por padrão, hoje).

    A referência é injetável para manter os testes determinísticos (seção 19).
    """
    today = reference if reference is not None else date.today()
    compared = value.date() if isinstance(value, datetime) else value
    return compared > today


__all__ = [
    "DATETIME_FORMATS",
    "DATE_FORMATS",
    "is_future",
    "parse_date",
    "parse_datetime",
]
