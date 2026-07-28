"""Testes do extrator de TXT."""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.application.dto.extraction import ExtractionOptions
from waypoint_etl.demo.document_files import TXT_TITLE, write_customers_txt
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import ExtractionError, SourceNotFoundError
from waypoint_etl.infrastructure.extractors.txt_extractor import TxtExtractor


@pytest.fixture
def extractor() -> TxtExtractor:
    return TxtExtractor()


def test_supports_only_txt(extractor: TxtExtractor) -> None:
    assert extractor.supports(Path("a.txt"))
    assert extractor.supports(Path("A.TXT"))
    assert not extractor.supports(Path("a.docx"))


def test_reads_content_as_single_page(extractor: TxtExtractor, tmp_path: Path) -> None:
    source = tmp_path / "a.txt"
    source.write_text("Nome: Ana\nCPF: 123", encoding="utf-8")

    result = extractor.extract_text(source)

    assert result.source_format is SourceFormat.TXT
    assert result.source_name == "a.txt"
    assert result.page_count == 1
    assert result.pages[0].number == 1
    assert result.text == "Nome: Ana\nCPF: 123"
    assert result.ocr_used is False
    assert result.warnings == ()


def test_cp1252_file_is_read_with_warning(
    extractor: TxtExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.txt"
    source.write_text("João Ação", encoding="cp1252")

    result = extractor.extract_text(source)

    assert result.text == "João Ação"
    assert any("codificação" in warning for warning in result.warnings)


def test_explicit_encoding_is_respected(
    extractor: TxtExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.txt"
    source.write_text("João", encoding="cp1252")

    result = extractor.extract_text(source, ExtractionOptions(encoding="cp1252"))

    assert result.text == "João"
    assert result.warnings == ()


def test_empty_file_is_reported_but_not_fatal(
    extractor: TxtExtractor, tmp_path: Path
) -> None:
    """Arquivo vazio vira aviso: quem decide o OCR é o estágio seguinte."""
    source = tmp_path / "a.txt"
    source.write_text("   \n\n", encoding="utf-8")

    result = extractor.extract_text(source)

    assert result.is_empty
    assert result.empty_pages == (1,)
    assert any("texto aproveitável" in warning for warning in result.warnings)


def test_unknown_encoding_raises_extraction_error(
    extractor: TxtExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.txt"
    source.write_text("Ana", encoding="utf-8")

    with pytest.raises(ExtractionError, match="Codificação desconhecida"):
        extractor.extract_text(source, ExtractionOptions(encoding="nao-existe"))


def test_missing_file_raises_source_not_found(
    extractor: TxtExtractor, tmp_path: Path
) -> None:
    with pytest.raises(SourceNotFoundError):
        extractor.extract_text(tmp_path / "inexistente.txt")


def test_demo_report_is_readable(extractor: TxtExtractor, tmp_path: Path) -> None:
    source = write_customers_txt(tmp_path / "clientes.txt", count=4)

    result = extractor.extract_text(source)

    assert TXT_TITLE in result.text
    assert result.text.count("CPF/CNPJ:") == 4
    assert not result.is_empty
