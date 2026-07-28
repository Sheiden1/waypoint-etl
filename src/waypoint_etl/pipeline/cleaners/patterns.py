"""Extração de padrões brasileiros em texto livre (documentos e OCR).

Regex aqui serve para **reconhecer e extrair** padrões de um texto não
estruturado, não para validar (seção 11). Um CPF extraído continua passando
pelos dígitos verificadores depois; um e-mail extraído continua sendo validado.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

from ...domain.value_objects.document import (
    is_valid_cnpj,
    is_valid_cpf,
    only_digits,
)

# Bordas com (?<!\d) e (?!\d) evitam capturar um trecho de número maior.
CPF_PATTERN = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
CNPJ_PATTERN = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?55[\s-]?)?\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}(?!\d)"
)
POSTAL_CODE_PATTERN = re.compile(r"(?<!\d)\d{5}-?\d{3}(?!\d)")
DATE_PATTERN = re.compile(
    r"(?<!\d)(?:\d{2}[/.-]\d{2}[/.-]\d{4}|\d{4}-\d{2}-\d{2})(?!\d)"
)
MONEY_PATTERN = re.compile(
    r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?|(?<![\d,.])\d{1,3}(?:\.\d{3})+,\d{2}(?![\d])"
)


def _unique(values: Iterator[str]) -> list[str]:
    """Remove repetições preservando a ordem de aparição no texto."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def find_cpfs(text: str) -> list[str]:
    """Extrai CPFs válidos (somente dígitos), já conferidos pelos verificadores.

    O padrão sozinho casaria com qualquer sequência de 11 dígitos; a validação
    evita devolver números de protocolo ou de série como se fossem CPF.
    """
    return _unique(
        only_digits(match)
        for match in CPF_PATTERN.findall(text)
        if is_valid_cpf(match)
    )


def find_cnpjs(text: str) -> list[str]:
    """Extrai CNPJs válidos (somente dígitos)."""
    return _unique(
        only_digits(match)
        for match in CNPJ_PATTERN.findall(text)
        if is_valid_cnpj(match)
    )


def find_documents(text: str) -> list[str]:
    """Extrai todos os CPFs e CNPJs válidos encontrados."""
    return _unique(iter(find_cnpjs(text) + find_cpfs(text)))


def find_emails(text: str) -> list[str]:
    """Extrai e-mails, normalizados para minúsculas."""
    return _unique(match.lower() for match in EMAIL_PATTERN.findall(text))


def find_phones(text: str) -> list[str]:
    """Extrai telefones em formato bruto, como aparecem no texto."""
    return _unique(match.strip() for match in PHONE_PATTERN.findall(text))


def find_postal_codes(text: str) -> list[str]:
    """Extrai CEPs em formato bruto."""
    return _unique(iter(POSTAL_CODE_PATTERN.findall(text)))


def find_dates(text: str) -> list[str]:
    """Extrai datas em formato bruto (a conversão fica com ``parse_date``)."""
    return _unique(iter(DATE_PATTERN.findall(text)))


def find_money_values(text: str) -> list[str]:
    """Extrai valores monetários em formato bruto."""
    return _unique(match.strip() for match in MONEY_PATTERN.findall(text))


def find_labeled_value(text: str, label: str) -> str | None:
    """Extrai o valor que segue um rótulo (``Nome: Ana Silva`` -> ``Ana Silva``).

    Aceita ``:`` ou ``|`` como separador, cobrindo tanto fichas em texto quanto
    as tabelas rótulo/valor extraídas de DOCX.
    """
    pattern = re.compile(
        rf"^\s*{re.escape(label)}\s*[:|]\s*(.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    if match is None:
        return None
    value = match.group(1).strip()
    return value or None


__all__ = [
    "CNPJ_PATTERN",
    "CPF_PATTERN",
    "DATE_PATTERN",
    "EMAIL_PATTERN",
    "MONEY_PATTERN",
    "PHONE_PATTERN",
    "POSTAL_CODE_PATTERN",
    "find_cnpjs",
    "find_cpfs",
    "find_dates",
    "find_documents",
    "find_emails",
    "find_labeled_value",
    "find_money_values",
    "find_phones",
    "find_postal_codes",
]
