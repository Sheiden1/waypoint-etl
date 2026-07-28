"""Extrator de documentos Word (``.docx``).

Fichas cadastrais e contratos costumam misturar parágrafos e tabelas, e a ordem
entre eles carrega significado ("Nome:" seguido do valor). Por isso o corpo do
documento é percorrido na ordem original, e não parágrafos primeiro.

O python-docx apenas lê o XML do pacote: macros nunca são executadas
(seção 18). Arquivos ``.docm`` não são aceitos.
"""

from __future__ import annotations

import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from ...application.dto.document import DocumentText, PageText
from ...application.dto.extraction import ExtractionOptions
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import ExtractionError
from .base import ensure_readable_file

SUPPORTED_SUFFIXES = frozenset({".docx"})

# Separador entre células de uma mesma linha de tabela. Mantém o par
# rótulo/valor legível para a extração por Regex do Dia 5.
CELL_SEPARATOR = " | "


class DocxExtractor:
    """Lê documentos ``.docx`` preservando a ordem de parágrafos e tabelas."""

    @property
    def source_format(self) -> SourceFormat:
        return SourceFormat.DOCX

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        ensure_readable_file(path)
        document = _open_document(path)

        blocks = [block for block in _iter_blocks(document) if block.strip()]
        warnings: list[str] = []
        if not blocks:
            warnings.append(
                "O documento não possui texto: pode ser um arquivo só com imagens."
            )

        return DocumentText(
            source_name=path.name,
            source_format=SourceFormat.DOCX,
            # O DOCX não expõe quebras de página confiáveis sem renderizar:
            # todo o corpo é tratado como uma única página.
            pages=(PageText(number=1, text="\n".join(blocks)),),
            warnings=tuple(warnings),
        )


def _open_document(path: Path) -> Any:
    """Abre o pacote DOCX, traduzindo falhas para um erro controlado."""
    try:
        return Document(str(path))
    except (
        PackageNotFoundError,
        zipfile.BadZipFile,
        KeyError,
        ValueError,
        OSError,
    ) as error:
        raise ExtractionError(
            f"'{path.name}' não é um documento Word válido. "
            "Formato aceito: .docx. Converta arquivos .doc antes de usar."
        ) from error


def _iter_blocks(document: Any) -> Iterator[str]:
    """Percorre o corpo do documento devolvendo o texto de cada bloco."""
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document).text
        elif isinstance(child, CT_Tbl):
            yield from _iter_table_rows(Table(child, document))


def _iter_table_rows(table: Any) -> Iterator[str]:
    """Converte cada linha da tabela em uma linha de texto."""
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        if any(cells):
            yield CELL_SEPARATOR.join(cells)


__all__ = ["CELL_SEPARATOR", "SUPPORTED_SUFFIXES", "DocxExtractor"]
