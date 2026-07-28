"""Caso de uso: inspecionar um arquivo de origem antes de migrar.

Responde "o que tem neste arquivo?" sem aplicar template nem validação. É o que
alimenta tanto o comando ``inspect`` quanto a etapa 1 do assistente Streamlit.
"""

from __future__ import annotations

from pathlib import Path

from ...domain.enums.source_format import SourceFormat
from ...infrastructure.extractors.registry import (
    detect_format,
    get_document_extractor,
    get_tabular_extractor,
    is_tabular,
)
from ...logging import get_logger
from ..dto.extraction import ExtractionOptions
from ..dto.results import SourcePreview
from ..ports.ocr import OcrEngine

# Quantas linhas da origem entram na prévia. Suficiente para conferir o
# cabeçalho e o formato dos valores sem despejar o arquivo inteiro na tela.
PREVIEW_ROWS = 10

# Trecho de texto exibido para documentos.
PREVIEW_CHARACTERS = 2000

_logger = get_logger(__name__)


def inspect_source(
    path: Path,
    *,
    options: ExtractionOptions | None = None,
    ocr_engine: OcrEngine | None = None,
) -> SourcePreview:
    """Detecta o formato de ``path`` e devolve uma prévia do conteúdo."""
    source_format = detect_format(path)
    _logger.info("Inspecionando arquivo", extra={"file": path.name})

    if is_tabular(path):
        return _inspect_tabular(path, source_format, options)
    return _inspect_document(path, source_format, options, ocr_engine)


def _inspect_tabular(
    path: Path, source_format: SourceFormat, options: ExtractionOptions | None
) -> SourcePreview:
    """Prévia de CSV/Excel: colunas e primeiras linhas."""
    extractor = get_tabular_extractor(path)
    result = extractor.extract(path, options)

    return SourcePreview(
        source_name=result.source_name,
        source_format=source_format,
        is_tabular=True,
        columns=result.columns,
        rows=tuple(record.values for record in result.records[:PREVIEW_ROWS]),
        available_sheets=result.available_sheets,
        warnings=result.warnings,
    )


def _inspect_document(
    path: Path,
    source_format: SourceFormat,
    options: ExtractionOptions | None,
    ocr_engine: OcrEngine | None,
) -> SourcePreview:
    """Prévia de TXT/DOCX/PDF/imagem: trecho do texto extraído."""
    extractor = get_document_extractor(path, ocr_engine=ocr_engine)
    if ocr_engine is not None and source_format is SourceFormat.PDF:
        from ...infrastructure.ocr.fallback import DocumentExtractorWithOcr

        extractor = DocumentExtractorWithOcr(extractor, ocr_engine)

    document = extractor.extract_text(path, options)
    text = document.text

    return SourcePreview(
        source_name=document.source_name,
        source_format=source_format,
        is_tabular=False,
        text_preview=text[:PREVIEW_CHARACTERS],
        page_count=document.page_count,
        ocr_used=document.ocr_used,
        warnings=document.warnings,
    )


__all__ = ["PREVIEW_CHARACTERS", "PREVIEW_ROWS", "inspect_source"]
