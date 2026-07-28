"""Testes da detecção de formato e seleção de extrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import UnsupportedFormatError
from waypoint_etl.infrastructure.extractors import (
    CsvExtractor,
    DocxExtractor,
    ExcelExtractor,
    PdfExtractor,
    TxtExtractor,
    detect_format,
    get_document_extractor,
    get_tabular_extractor,
    is_tabular,
)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("a.csv", SourceFormat.CSV),
        ("a.CSV", SourceFormat.CSV),
        ("a.xlsx", SourceFormat.EXCEL),
        ("a.xlsm", SourceFormat.EXCEL),
        ("a.pdf", SourceFormat.PDF),
        ("a.docx", SourceFormat.DOCX),
        ("a.txt", SourceFormat.TXT),
        ("a.png", SourceFormat.IMAGE),
        ("a.jpg", SourceFormat.IMAGE),
        ("a.jpeg", SourceFormat.IMAGE),
    ],
)
def test_detect_format(filename: str, expected: SourceFormat) -> None:
    assert detect_format(Path(filename)) is expected


@pytest.mark.parametrize("filename", ["a.xls", "a.json", "arquivo_sem_extensao"])
def test_detect_format_rejects_unknown_extensions(filename: str) -> None:
    with pytest.raises(UnsupportedFormatError):
        detect_format(Path(filename))


@pytest.mark.parametrize(
    ("filename", "expected"),
    [("a.csv", True), ("a.xlsx", True), ("a.pdf", False), ("a.txt", False)],
)
def test_is_tabular(filename: str, expected: bool) -> None:
    assert is_tabular(Path(filename)) is expected


def test_get_tabular_extractor_returns_implementation() -> None:
    assert isinstance(get_tabular_extractor(Path("a.csv")), CsvExtractor)
    assert isinstance(get_tabular_extractor(Path("a.xlsx")), ExcelExtractor)


def test_get_document_extractor_returns_implementation() -> None:
    assert isinstance(get_document_extractor(Path("a.txt")), TxtExtractor)
    assert isinstance(get_document_extractor(Path("a.docx")), DocxExtractor)
    assert isinstance(get_document_extractor(Path("a.pdf")), PdfExtractor)


@pytest.mark.parametrize("filename", ["a.pdf", "a.docx", "a.txt"])
def test_tabular_extractor_rejects_documents_with_guidance(filename: str) -> None:
    with pytest.raises(UnsupportedFormatError, match="não tabular"):
        get_tabular_extractor(Path(filename))


@pytest.mark.parametrize("filename", ["a.csv", "a.xlsx"])
def test_document_extractor_rejects_tabular_with_guidance(filename: str) -> None:
    with pytest.raises(UnsupportedFormatError, match="não um documento"):
        get_document_extractor(Path(filename))


@pytest.mark.parametrize("filename", ["a.png", "a.jpg", "a.jpeg"])
def test_images_require_an_ocr_engine(filename: str) -> None:
    """Imagem não tem camada de texto: sem motor de OCR, falha explicitamente."""
    with pytest.raises(UnsupportedFormatError, match="só podem ser lidas por OCR"):
        get_document_extractor(Path(filename))
