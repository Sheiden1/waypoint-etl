"""Testes do extrator de imagens."""

from __future__ import annotations

from pathlib import Path

import pytest

from support.ocr import BrokenOcrEngine, FakeOcrEngine
from waypoint_etl.demo.document_files import write_scanned_form_image
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import (
    ExtractionError,
    SourceNotFoundError,
    UnsupportedFormatError,
)
from waypoint_etl.infrastructure.extractors import get_document_extractor
from waypoint_etl.infrastructure.extractors.image_extractor import ImageExtractor


@pytest.fixture
def scan(tmp_path: Path) -> Path:
    return write_scanned_form_image(tmp_path / "ficha.png")


def test_supports_image_formats() -> None:
    extractor = ImageExtractor(FakeOcrEngine())

    assert extractor.supports(Path("a.png"))
    assert extractor.supports(Path("a.JPG"))
    assert extractor.supports(Path("a.jpeg"))
    assert not extractor.supports(Path("a.pdf"))


def test_reads_text_from_an_image(scan: Path) -> None:
    engine = FakeOcrEngine()

    result = ImageExtractor(engine).extract_text(scan)

    assert result.source_format is SourceFormat.IMAGE
    assert result.ocr_used is True
    assert result.page_count == 1
    assert "Ana Maria Silva" in result.text
    assert engine.calls == 1


def test_image_result_is_always_flagged_for_review(scan: Path) -> None:
    result = ImageExtractor(FakeOcrEngine()).extract_text(scan)

    assert any("OCR" in warning for warning in result.warnings)


def test_blank_ocr_result_is_reported(scan: Path) -> None:
    result = ImageExtractor(FakeOcrEngine(text="  ")).extract_text(scan)

    assert result.is_empty
    assert any("não reconheceu" in warning for warning in result.warnings)


def test_missing_engine_fails_explicitly(scan: Path) -> None:
    """Sem OCR não há como ler uma imagem: falhar é mais honesto que devolver vazio."""
    extractor = ImageExtractor(FakeOcrEngine(available=False))

    with pytest.raises(ExtractionError, match="Tesseract"):
        extractor.extract_text(scan)


def test_engine_failure_becomes_a_controlled_error(scan: Path) -> None:
    with pytest.raises(ExtractionError, match="Não foi possível processar"):
        ImageExtractor(BrokenOcrEngine()).extract_text(scan)


def test_missing_file_raises_source_not_found(tmp_path: Path) -> None:
    with pytest.raises(SourceNotFoundError):
        ImageExtractor(FakeOcrEngine()).extract_text(tmp_path / "nao_existe.png")


def test_registry_returns_the_image_extractor_when_ocr_is_provided() -> None:
    extractor = get_document_extractor(Path("a.png"), ocr_engine=FakeOcrEngine())

    assert isinstance(extractor, ImageExtractor)


def test_registry_explains_that_images_need_ocr() -> None:
    with pytest.raises(UnsupportedFormatError, match="só podem ser lidas por OCR"):
        get_document_extractor(Path("a.png"))
