"""Exportação dos resultados de uma execução (seção 16).

Cada execução produz ``exports/<run_id>/`` com quatro arquivos. O ``accepted``
carrega o dado real, porque é a carga de importação; o ``rejected`` preserva os
valores de origem para que o usuário consiga corrigi-los na planilha original.
O mascaramento de documentos é aplicado no relatório de auditoria, que é o
artefato de leitura (seção 18).
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import fields as dataclass_fields
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path

from openpyxl import Workbook

from ...domain.enums.entity_type import EntityType
from ...domain.services.canonical_schema import field_names
from ...pipeline.deduplication.detector import DeduplicationResult
from ...pipeline.validators.result import ValidatedRecord

ACCEPTED_FILENAME = "accepted.csv"
REJECTED_FILENAME = "rejected.xlsx"
DUPLICATES_FILENAME = "duplicates.csv"

REJECTED_SHEET_NAME = "Rejeitados"

# Colunas fixas do relatório de rejeitados, antes dos valores de origem.
_REJECTED_HEADERS = ("linha", "aba", "campo", "codigo", "severidade", "mensagem")

_DUPLICATE_HEADERS = (
    "linha",
    "linha_correspondente",
    "tipo",
    "chave",
    "valor",
    "similaridade",
)


def run_output_dir(base_dir: Path, run_id: str) -> Path:
    """Diretório da execução: ``<base>/<run_id>/``."""
    return base_dir / run_id


def export_accepted(
    path: Path, records: Sequence[ValidatedRecord], entity: EntityType
) -> Path:
    """Escreve os registros válidos em CSV, no schema canônico."""
    columns = field_names(entity)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for record in records:
            if record.entity is None:
                continue
            writer.writerow(_entity_to_row(record.entity, columns))

    return path


def export_rejected(path: Path, records: Sequence[ValidatedRecord]) -> Path:
    """Escreve os registros rejeitados em XLSX, uma linha por problema.

    Uma linha por problema (e não por registro) porque o usuário corrige campo a
    campo; agrupar tudo em uma célula tornaria a planilha inútil.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    source_columns = _source_columns(records)

    workbook = Workbook()
    default_sheet = workbook.active
    if default_sheet is not None:
        workbook.remove(default_sheet)

    sheet = workbook.create_sheet(REJECTED_SHEET_NAME)
    sheet.append([*_REJECTED_HEADERS, *source_columns])

    for record in records:
        values = [record.values.get(column) for column in source_columns]
        for issue in record.errors:
            sheet.append(
                [
                    record.row_number,
                    record.sheet,
                    issue.field,
                    issue.code,
                    issue.severity.value,
                    issue.message,
                    *values,
                ]
            )

    workbook.save(path)
    workbook.close()
    return path


def export_duplicates(path: Path, duplicates: DeduplicationResult) -> Path:
    """Escreve as duplicidades encontradas em CSV.

    Duplicatas exatas e suspeitas ficam no mesmo arquivo, distinguidas pela
    coluna ``tipo``: quem revisa precisa ver as duas listas lado a lado.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(_DUPLICATE_HEADERS)

        for match in duplicates.exact:
            writer.writerow(
                [
                    match.row_number,
                    match.matched_row_number,
                    "exata",
                    match.key,
                    match.value,
                    "",
                ]
            )
        for match in duplicates.possible:
            writer.writerow(
                [
                    match.row_number,
                    match.matched_row_number,
                    "possivel",
                    match.key,
                    match.value,
                    f"{match.similarity:.3f}",
                ]
            )

    return path


def _source_columns(records: Sequence[ValidatedRecord]) -> tuple[str, ...]:
    """Colunas canônicas presentes nos registros, preservando a ordem."""
    columns: list[str] = []
    for record in records:
        for key in record.values:
            if key not in columns:
                columns.append(key)
    return tuple(columns)


def _entity_to_row(entity: object, columns: Sequence[str]) -> dict[str, str]:
    """Converte uma entidade canônica em uma linha de texto para CSV."""
    data = {
        field.name: getattr(entity, field.name)
        for field in dataclass_fields(entity)  # type: ignore[arg-type]
    }
    return {column: _format_value(data.get(column)) for column in columns}


def _format_value(value: object) -> str:
    """Serializa um valor canônico preservando precisão e formato ISO."""
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Decimal):
        # ``str`` mantém a escala; ``float`` perderia centavos.
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


__all__ = [
    "ACCEPTED_FILENAME",
    "DUPLICATES_FILENAME",
    "REJECTED_FILENAME",
    "export_accepted",
    "export_duplicates",
    "export_rejected",
    "run_output_dir",
]
