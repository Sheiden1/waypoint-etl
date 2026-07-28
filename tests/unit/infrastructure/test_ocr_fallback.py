"""Testes do fallback automático para OCR (seção 12).

A lógica de decisão é testada com um motor de OCR falso e determinístico, sem
depender do binário do Tesseract estar instalado.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from support.ocr import BrokenOcrEngine, FakeOcrEngine
from waypoint_etl.application.dto.document import DocumentText, PageText
from waypoint_etl.demo.document_files import write_scanned_form_pdf
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.infrastructure.extractors.pdf_extractor import PdfExtractor
from waypoint_etl.infrastructure.ocr.fallback import DocumentExtractorWithOcr


def _write_digital_pdf(path: Path, body: str) -> Path:
    document = pymupdf.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), body, fontsize=11, fontname="helv")
        document.save(path)
    finally:
        document.close()
    return path


@pytest.fixture
def scanned_pdf(tmp_path: Path) -> Path:
    return write_scanned_form_pdf(tmp_path / "escaneada.pdf", count=2)


# --- Quando NÃO usar OCR ------------------------------------------------------


def test_digital_pdf_does_not_trigger_ocr(tmp_path: Path) -> None:
    """Seção 12: OCR só quando a extração nativa for insuficiente."""
    source = _write_digital_pdf(
        tmp_path / "digital.pdf", "Nome: Ana Silva\nCPF: 390.533.447-05"
    )
    engine = FakeOcrEngine()

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(source)

    assert engine.calls == 0
    assert result.ocr_used is False
    assert "Ana Silva" in result.text


def test_native_text_is_preferred_over_ocr(tmp_path: Path) -> None:
    source = _write_digital_pdf(tmp_path / "digital.pdf", "CPF: 390.533.447-05")
    engine = FakeOcrEngine(text="TEXTO DE OCR")

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(source)

    assert "TEXTO DE OCR" not in result.text


# --- Quando usar OCR ----------------------------------------------------------


def test_scanned_pdf_triggers_ocr(scanned_pdf: Path) -> None:
    engine = FakeOcrEngine()

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(scanned_pdf)

    assert engine.calls == 2
    assert result.ocr_used is True
    assert "Ana Maria Silva" in result.text


def test_ocr_usage_is_recorded_in_the_report(scanned_pdf: Path) -> None:
    """Seção 12, item 6: registrar no relatório se o OCR foi utilizado."""
    result = DocumentExtractorWithOcr(PdfExtractor(), FakeOcrEngine()).extract_text(
        scanned_pdf
    )

    assert result.ocr_used is True
    assert any("OCR aplicado" in warning for warning in result.warnings)


def test_ocr_result_is_flagged_as_needing_review(scanned_pdf: Path) -> None:
    """Seção 12, item 7: nunca tratar o OCR como confiável."""
    result = DocumentExtractorWithOcr(PdfExtractor(), FakeOcrEngine()).extract_text(
        scanned_pdf
    )

    assert any("não é confiável" in warning for warning in result.warnings)


def test_only_the_insufficient_pages_are_processed(tmp_path: Path) -> None:
    """Renderizar página é caro: só as vazias devem passar pelo OCR."""
    document = pymupdf.open()
    try:
        first = document.new_page()
        first.insert_text(
            (72, 72), "CPF: 390.533.447-05", fontsize=11, fontname="helv"
        )
        document.new_page()  # página sem texto
        source = tmp_path / "misto.pdf"
        document.save(source)
    finally:
        document.close()

    engine = FakeOcrEngine()
    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(source)

    assert engine.calls == 1
    assert result.ocr_used is True
    assert "390.533.447-05" in result.pages[0].text
    assert "Ana Maria Silva" in result.pages[1].text


# --- Degradação controlada ----------------------------------------------------


def test_missing_tesseract_warns_instead_of_failing(scanned_pdf: Path) -> None:
    """Sem OCR o documento não é lido, mas o lote não quebra."""
    engine = FakeOcrEngine(available=False)

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(scanned_pdf)

    assert engine.calls == 0
    assert result.ocr_used is False
    assert any("OCR não está disponível" in warning for warning in result.warnings)


def test_engine_failure_keeps_the_other_pages(scanned_pdf: Path) -> None:
    engine = BrokenOcrEngine()

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(scanned_pdf)

    assert result.ocr_used is False
    assert result.page_count == 2
    assert any("não conseguiu extrair" in warning for warning in result.warnings)


def test_ocr_returning_blank_text_is_reported(scanned_pdf: Path) -> None:
    engine = FakeOcrEngine(text="   \n  ")

    result = DocumentExtractorWithOcr(PdfExtractor(), engine).extract_text(scanned_pdf)

    assert result.ocr_used is False
    assert any("não conseguiu extrair" in warning for warning in result.warnings)


# --- Contrato do decorador ----------------------------------------------------


def test_decorator_preserves_the_extractor_interface() -> None:
    decorated = DocumentExtractorWithOcr(PdfExtractor(), FakeOcrEngine())

    assert decorated.source_format is SourceFormat.PDF
    assert decorated.supports(Path("a.pdf"))
    assert not decorated.supports(Path("a.docx"))


def test_non_pdf_documents_are_returned_untouched(tmp_path: Path) -> None:
    """Só PDF pode ser rasterizado; TXT/DOCX vazios não viram OCR."""

    class EmptyTxtExtractor:
        @property
        def source_format(self) -> SourceFormat:
            return SourceFormat.TXT

        def supports(self, path: Path) -> bool:
            return True

        def extract_text(self, path: Path, options: object = None) -> DocumentText:
            return DocumentText(
                source_name=path.name,
                source_format=SourceFormat.TXT,
                pages=(PageText(number=1, text=""),),
            )

    engine = FakeOcrEngine()
    decorated = DocumentExtractorWithOcr(EmptyTxtExtractor(), engine)

    result = decorated.extract_text(tmp_path / "vazio.txt")

    assert engine.calls == 0
    assert result.ocr_used is False
