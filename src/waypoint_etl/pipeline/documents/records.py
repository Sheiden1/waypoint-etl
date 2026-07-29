"""Estruturação de documentos textuais em registros.

Documentos não têm linhas e colunas, então a extração devolve texto por página
(``DocumentText``). Este módulo fecha a lacuna entre esse texto e o restante do
pipeline: ele reconhece pares ``Rótulo: valor`` e devolve um
``ExtractionResult`` idêntico ao que CSV e Excel produzem. Com isso, De/Para,
validação, deduplicação, exportação e auditoria funcionam sem alteração.

O reconhecimento é deliberadamente simples e auditável. Ele não adivinha campos
nem infere significado: um rótulo vira coluna, e o template decide o destino.
"""

from __future__ import annotations

import re

from ...application.dto.document import DocumentText
from ...application.dto.extraction import ExtractionResult, SourceRecord
from ...domain.errors import WaypointError
from ..mappers.schema import RecordMode, SourceSpec

_MAX_LABEL_LENGTH = 60


class DocumentStructureError(WaypointError):
    """O documento não pôde ser dividido em registros."""


def parse_document_records(
    document: DocumentText, source: SourceSpec
) -> ExtractionResult:
    """Converte o texto de um documento em registros rotulados.

    ``RecordMode.PAGE`` trata cada página como um registro — o formato de ficha,
    uma por página. ``RecordMode.SEPARATOR`` divide o texto por uma expressão
    regular, para relatórios em texto corrido com marcador entre registros.
    """
    blocks = _split_into_blocks(document, source)
    records: list[SourceRecord] = []
    columns: list[str] = []

    for origin, block in blocks:
        values = _labelled_values(block, source.label_separator)
        if not values:
            continue
        for label in values:
            if label not in columns:
                columns.append(label)
        records.append(SourceRecord(row_number=origin, values=dict(values)))

    if not records:
        raise DocumentStructureError(
            f"Nenhum registro foi reconhecido em '{document.source_name}'. "
            f"O documento precisa conter pares no formato "
            f"'Rótulo{source.label_separator} valor'. "
            "Confira o template ou revise a qualidade da extração."
        )

    warnings = document.warnings
    if document.ocr_used:
        warnings += (
            "Os registros vieram de texto reconhecido por OCR. "
            "Confira os valores antes de considerar a migração final.",
        )

    return ExtractionResult(
        source_name=document.source_name,
        source_format=document.source_format,
        columns=tuple(columns),
        records=tuple(records),
        ocr_used=document.ocr_used,
        warnings=warnings,
    )


def _split_into_blocks(
    document: DocumentText, source: SourceSpec
) -> list[tuple[int, str]]:
    """Divide o documento em blocos, preservando a origem de cada um.

    A origem é o número da página no modo página e a posição do bloco no modo
    separador, para que uma rejeição possa ser rastreada até o documento.
    """
    if source.record_mode is RecordMode.PAGE:
        return [(page.number, page.text) for page in document.pages]

    if not source.record_separator:
        raise DocumentStructureError(
            "'source.record_separator' é obrigatório quando "
            "'source.record_mode' é 'separator'."
        )
    try:
        pattern = re.compile(source.record_separator, re.MULTILINE)
    except re.error as error:
        raise DocumentStructureError(
            f"'source.record_separator' não é uma expressão regular válida: "
            f"{error}."
        ) from error

    parts = pattern.split(document.text)
    return [(position, part) for position, part in enumerate(parts, start=1)]


def _labelled_values(block: str, label_separator: str) -> dict[str, str | None]:
    """Extrai os pares ``Rótulo: valor`` de um bloco de texto.

    Linhas sem separador são ignoradas: cabeçalhos e molduras de relatório não
    devem virar campo. Um rótulo repetido no mesmo bloco mantém a primeira
    ocorrência, porque a segunda costuma ser rodapé ou repetição de moldura.
    """
    values: dict[str, str | None] = {}

    for line in block.splitlines():
        label, separator, raw_value = line.partition(label_separator)
        if not separator:
            continue
        label = label.strip()
        if not label or len(label) > _MAX_LABEL_LENGTH or label in values:
            continue
        value = raw_value.strip()
        values[label] = value or None

    return values


__all__ = ["DocumentStructureError", "parse_document_records"]
