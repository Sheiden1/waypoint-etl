"""Detecção do formato de origem e seleção do extrator correspondente.

Existem dois tipos de extrator porque existem dois tipos de resultado: fontes
tabulares devolvem registros; documentos devolvem texto para estruturação
posterior por Regex.
"""

from __future__ import annotations

from pathlib import Path

from ...application.ports.extractor import DocumentExtractor, TabularExtractor
from ...application.ports.ocr import OcrEngine
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import UnsupportedFormatError
from .csv_extractor import CsvExtractor
from .docx_extractor import DocxExtractor
from .excel_extractor import ExcelExtractor
from .image_extractor import ImageExtractor
from .pdf_extractor import PdfExtractor
from .txt_extractor import TxtExtractor

# Formatos declarados no escopo do MVP (seção 4), mesmo os ainda não
# implementados: a detecção precisa distinguir "não suportado" de "pendente".
EXTENSION_FORMATS: dict[str, SourceFormat] = {
    ".csv": SourceFormat.CSV,
    ".xlsx": SourceFormat.EXCEL,
    ".xlsm": SourceFormat.EXCEL,
    ".pdf": SourceFormat.PDF,
    ".docx": SourceFormat.DOCX,
    ".txt": SourceFormat.TXT,
    ".png": SourceFormat.IMAGE,
    ".jpg": SourceFormat.IMAGE,
    ".jpeg": SourceFormat.IMAGE,
}

TABULAR_FORMATS = frozenset({SourceFormat.CSV, SourceFormat.EXCEL})
DOCUMENT_FORMATS = frozenset(
    {SourceFormat.PDF, SourceFormat.DOCX, SourceFormat.TXT, SourceFormat.IMAGE}
)


def _tabular_extractors() -> tuple[TabularExtractor, ...]:
    """Extratores tabulares disponíveis, na ordem de tentativa."""
    return (CsvExtractor(), ExcelExtractor())


def _document_extractors(
    ocr_engine: OcrEngine | None = None,
) -> tuple[DocumentExtractor, ...]:
    """Extratores de documento disponíveis, na ordem de tentativa.

    O extrator de imagens só entra na lista quando há um motor de OCR: sem ele,
    imagens falham com uma mensagem explícita em vez de devolver texto vazio.
    """
    extractors: list[DocumentExtractor] = [
        TxtExtractor(),
        DocxExtractor(),
        PdfExtractor(),
    ]
    if ocr_engine is not None:
        extractors.append(ImageExtractor(ocr_engine))
    return tuple(extractors)


def detect_format(path: Path) -> SourceFormat:
    """Identifica o formato pela extensão do arquivo.

    Levanta ``UnsupportedFormatError`` quando a extensão está fora do escopo.
    """
    suffix = path.suffix.lower()
    try:
        return EXTENSION_FORMATS[suffix]
    except KeyError:
        supported = ", ".join(sorted(EXTENSION_FORMATS))
        raise UnsupportedFormatError(
            f"Formato não suportado: '{suffix or path.name}'. "
            f"Extensões aceitas: {supported}."
        ) from None


def is_tabular(path: Path) -> bool:
    """Indica se ``path`` é uma fonte tabular (devolve registros diretamente)."""
    return detect_format(path) in TABULAR_FORMATS


def get_tabular_extractor(path: Path) -> TabularExtractor:
    """Devolve o extrator tabular capaz de ler ``path``."""
    source_format = detect_format(path)
    for extractor in _tabular_extractors():
        if extractor.supports(path):
            return extractor
    if source_format in DOCUMENT_FORMATS:
        raise UnsupportedFormatError(
            f"'{source_format.value}' é um formato de documento, não tabular. "
            "Use o extrator de documentos para este arquivo."
        )
    raise UnsupportedFormatError(  # pragma: no cover - guarda para novos formatos
        f"O formato '{source_format.value}' ainda não possui extrator tabular."
    )


def get_document_extractor(
    path: Path, *, ocr_engine: OcrEngine | None = None
) -> DocumentExtractor:
    """Devolve o extrator de documentos capaz de ler ``path``.

    Formatos que dependem de um recurso ausente falham com uma mensagem
    explícita, nunca com um resultado simulado.
    """
    source_format = detect_format(path)
    for extractor in _document_extractors(ocr_engine):
        if extractor.supports(path):
            return extractor
    if source_format in TABULAR_FORMATS:
        raise UnsupportedFormatError(
            f"'{source_format.value}' é um formato tabular, não um documento. "
            "Use o extrator tabular para este arquivo."
        )
    if source_format is SourceFormat.IMAGE:
        raise UnsupportedFormatError(
            "Imagens só podem ser lidas por OCR. Informe um motor de OCR em "
            "'ocr_engine' e verifique se o Tesseract está instalado."
        )
    raise UnsupportedFormatError(  # pragma: no cover - guarda para novos formatos
        f"O formato '{source_format.value}' ainda não possui extrator "
        "implementado nesta versão do Waypoint."
    )


__all__ = [
    "DOCUMENT_FORMATS",
    "EXTENSION_FORMATS",
    "TABULAR_FORMATS",
    "detect_format",
    "get_document_extractor",
    "get_tabular_extractor",
    "is_tabular",
]
