"""Testes do extrator de PDF digital (camada de texto nativa)."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pymupdf
import pytest

from waypoint_etl.demo.document_files import FORM_TITLE, write_customer_form_pdf
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import ExtractionError, SourceNotFoundError
from waypoint_etl.infrastructure.extractors.pdf_extractor import (
    PdfExtractor,
    _iter_pages,
)


@pytest.fixture
def extractor() -> PdfExtractor:
    return PdfExtractor()


def _write_pdf(path: Path, pages: list[str]) -> Path:
    """Gera um PDF com uma página por item; string vazia = página sem texto."""
    document = pymupdf.open()
    try:
        for body in pages:
            page = document.new_page()
            if body:
                page.insert_text((72, 72), body, fontsize=11, fontname="helv")
        document.save(path)
    finally:
        document.close()
    return path


def test_supports_only_pdf(extractor: PdfExtractor) -> None:
    assert extractor.supports(Path("a.pdf"))
    assert extractor.supports(Path("A.PDF"))
    assert not extractor.supports(Path("a.docx"))


def test_reads_text_layer_per_page(extractor: PdfExtractor, tmp_path: Path) -> None:
    source = _write_pdf(tmp_path / "a.pdf", ["Nome: Ana Silva", "Nome: Bruno Souza"])

    result = extractor.extract_text(source)

    assert result.source_format is SourceFormat.PDF
    assert result.page_count == 2
    assert [page.number for page in result.pages] == [1, 2]
    assert "Nome: Ana Silva" in result.pages[0].text
    assert "Nome: Bruno Souza" in result.pages[1].text
    assert result.ocr_used is False
    assert result.warnings == ()


def test_never_runs_ocr(extractor: PdfExtractor, tmp_path: Path) -> None:
    """Este extrator só faz a etapa nativa da estratégia da seção 12."""
    source = _write_pdf(tmp_path / "a.pdf", [""])

    result = extractor.extract_text(source)

    assert result.ocr_used is False


def test_page_without_text_layer_is_flagged_for_ocr(
    extractor: PdfExtractor, tmp_path: Path
) -> None:
    source = _write_pdf(tmp_path / "a.pdf", ["Nome: Ana", "", "Nome: Bruno"])

    result = extractor.extract_text(source)

    assert result.page_count == 3
    assert result.empty_pages == (2,)
    assert any("Páginas sem camada de texto: 2" in w for w in result.warnings)


def test_fully_scanned_pdf_is_reported_as_needing_ocr(
    extractor: PdfExtractor, tmp_path: Path
) -> None:
    source = _write_pdf(tmp_path / "a.pdf", ["", ""])

    result = extractor.extract_text(source)

    assert result.is_empty
    assert result.empty_pages == (1, 2)
    assert any("provavelmente" in warning for warning in result.warnings)


def test_pdf_without_pages_raises_extraction_error(tmp_path: Path) -> None:
    """Um PDF sem páginas é falha de arquivo, não resultado vazio.

    O PyMuPDF se recusa a gravar um PDF de zero páginas, então a guarda é
    exercitada diretamente sobre o helper.
    """

    class EmptyPdf:
        pages: ClassVar[list[object]] = []

    with pytest.raises(ExtractionError, match="páginas legíveis"):
        list(_iter_pages(EmptyPdf(), tmp_path / "a.pdf"))


def test_malformed_page_becomes_empty_page_instead_of_failing() -> None:
    """Seção 17: um problema pontual não interrompe a leitura das demais."""

    class BrokenPage:
        def extract_text(self) -> str:
            raise RuntimeError("página corrompida")

        def flush_cache(self) -> None:
            return None

    class OkPage:
        def extract_text(self) -> str:
            return "Nome: Ana"

        def flush_cache(self) -> None:
            return None

    class Pdf:
        pages: ClassVar[list[object]] = [BrokenPage(), OkPage()]

    pages = list(_iter_pages(Pdf(), Path("a.pdf")))

    assert pages[0].is_empty
    assert pages[1].text == "Nome: Ana"


def test_password_protected_pdf_asks_user_to_remove_protection(
    extractor: PdfExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.pdf"
    document = pymupdf.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "Nome: Ana", fontsize=11, fontname="helv")
        document.save(
            source,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw="dono",
            user_pw="segredo",
        )
    finally:
        document.close()

    with pytest.raises(ExtractionError, match="protegido por senha"):
        extractor.extract_text(source)


def test_non_pdf_content_raises_extraction_error(
    extractor: PdfExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.pdf"
    source.write_text("isto não é um PDF", encoding="utf-8")

    with pytest.raises(ExtractionError):
        extractor.extract_text(source)


def test_missing_file_raises_source_not_found(
    extractor: PdfExtractor, tmp_path: Path
) -> None:
    with pytest.raises(SourceNotFoundError):
        extractor.extract_text(tmp_path / "inexistente.pdf")


def test_demo_form_is_readable(extractor: PdfExtractor, tmp_path: Path) -> None:
    source = write_customer_form_pdf(tmp_path / "ficha.pdf")

    result = extractor.extract_text(source)

    assert result.page_count == 3
    assert FORM_TITLE in result.text
    assert "CPF/CNPJ:" in result.text
    assert result.empty_pages == ()
