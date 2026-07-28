"""Utilitários compartilhados pelos extratores tabulares."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ...domain.errors import ExtractionError, SourceNotFoundError

# Placeholder para colunas sem cabeçalho, preservando a posição original.
UNNAMED_COLUMN_TEMPLATE = "coluna_{index}"

# Ordem de tentativa: exportações de ERPs legados costumam vir em UTF-8 (com ou
# sem BOM) ou em codificações Windows. ``latin-1`` nunca falha e fecha a lista.
ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def ensure_readable_file(path: Path) -> None:
    """Valida que ``path`` existe e é um arquivo regular.

    Levanta ``SourceNotFoundError`` com mensagem acionável, em vez de deixar
    vazar um ``OSError`` da biblioteca de leitura.
    """
    if not path.exists():
        raise SourceNotFoundError(
            f"Arquivo de origem não encontrado: {path}. Verifique o caminho informado."
        )
    if not path.is_file():
        raise SourceNotFoundError(
            f"O caminho informado não é um arquivo: {path}. "
            "Informe o arquivo, não o diretório."
        )


def read_text_file(path: Path, encoding: str | None) -> tuple[str, str]:
    """Lê um arquivo de texto, devolvendo ``(conteúdo, codificação usada)``.

    Quando ``encoding`` não é informado, tenta ``ENCODING_CANDIDATES`` em ordem.
    Compartilhado pelos extratores de CSV e TXT.
    """
    candidates = (encoding,) if encoding else ENCODING_CANDIDATES
    last_error: UnicodeDecodeError | None = None
    for candidate in candidates:
        try:
            return path.read_text(encoding=candidate), candidate
        except UnicodeDecodeError as error:
            last_error = error
        except LookupError as error:
            raise ExtractionError(
                f"Codificação desconhecida: '{candidate}'. "
                "Use um nome válido, como 'utf-8' ou 'cp1252'."
            ) from error
    raise ExtractionError(
        f"Não foi possível decodificar '{path.name}'. "
        "Informe a codificação correta no template De/Para."
    ) from last_error


def coerce_cell(value: object) -> str | None:
    """Converte uma célula para texto bruto, preservando o formato de origem.

    A extração não interpreta valores: datas e números viram texto estável e a
    conversão para tipos canônicos acontece nos normalizadores. Células vazias
    (ou só com espaços) viram ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dt.datetime):
        if (value.hour, value.minute, value.second, value.microsecond) == (0, 0, 0, 0):
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dt.time):
        return value.isoformat()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # Planilhas guardam inteiros como float; evita "1000.0" virar ruído.
        if value.is_integer():
            return str(int(value))
        return repr(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value).strip() or None


def normalize_headers(
    raw_headers: Sequence[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Normaliza os nomes das colunas e devolve ``(colunas, avisos)``.

    Cabeçalhos vazios recebem um nome posicional e nomes repetidos ganham um
    sufixo, para que nenhuma coluna de origem seja silenciosamente perdida.
    """
    columns: list[str] = []
    warnings: list[str] = []
    seen: dict[str, int] = {}

    for index, raw in enumerate(raw_headers, start=1):
        name = coerce_cell(raw)
        if name is None:
            name = UNNAMED_COLUMN_TEMPLATE.format(index=index)
            warnings.append(
                f"Coluna {index} está sem cabeçalho e foi nomeada como '{name}'."
            )
        name = " ".join(name.split())

        occurrences = seen.get(name, 0) + 1
        seen[name] = occurrences
        if occurrences > 1:
            unique = f"{name} ({occurrences})"
            warnings.append(
                f"Cabeçalho duplicado '{name}' renomeado para '{unique}'. "
                "Ajuste a origem ou o template De/Para se as colunas forem distintas."
            )
            name = unique

        columns.append(name)

    return tuple(columns), tuple(warnings)


def is_blank_row(values: Sequence[str | None]) -> bool:
    """Indica se a linha inteira está vazia (deve ser ignorada)."""
    return all(value is None for value in values)


def build_row_mapping(
    columns: Sequence[str], values: Sequence[str | None]
) -> dict[str, str | None]:
    """Associa valores às colunas, tolerando linhas curtas ou longas.

    Colunas ausentes viram ``None``; valores excedentes são descartados porque
    não existe destino possível para eles no template De/Para.
    """
    mapping: dict[str, str | None] = {}
    for index, column in enumerate(columns):
        mapping[column] = values[index] if index < len(values) else None
    return mapping


__all__ = [
    "ENCODING_CANDIDATES",
    "UNNAMED_COLUMN_TEMPLATE",
    "build_row_mapping",
    "coerce_cell",
    "ensure_readable_file",
    "is_blank_row",
    "normalize_headers",
    "read_text_file",
]
