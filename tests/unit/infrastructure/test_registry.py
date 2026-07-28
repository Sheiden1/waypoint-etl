"""Testes da detecção de formato e seleção de extrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import UnsupportedFormatError
from waypoint_etl.infrastructure.extractors import (
    CsvExtractor,
    ExcelExtractor,
    detect_format,
    get_extractor,
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


def test_get_extractor_returns_implementation() -> None:
    assert isinstance(get_extractor(Path("a.csv")), CsvExtractor)
    assert isinstance(get_extractor(Path("a.xlsx")), ExcelExtractor)


@pytest.mark.parametrize("filename", ["a.pdf", "a.docx", "a.txt", "a.png"])
def test_get_extractor_reports_pending_formats_explicitly(filename: str) -> None:
    """Formatos previstos mas não implementados falham em vez de simular."""
    with pytest.raises(UnsupportedFormatError, match="ainda não possui extrator"):
        get_extractor(Path(filename))
