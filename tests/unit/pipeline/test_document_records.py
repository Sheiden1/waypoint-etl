"""Estruturação de documentos textuais em registros rotulados."""

from __future__ import annotations

import pytest

from waypoint_etl.application.dto.document import DocumentText, PageText
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.pipeline.documents.records import (
    DocumentStructureError,
    parse_document_records,
)
from waypoint_etl.pipeline.mappers.schema import RecordMode, SourceSpec

FICHA = "Código: ERP-1\nNome: Ada Lovelace\nCPF/CNPJ: 111\n"
OUTRA = "Código: ERP-2\nNome: Grace Hopper\nCPF/CNPJ: 222\n"


def _document(*pages: str, ocr_used: bool = False) -> DocumentText:
    return DocumentText(
        source_name="fichas.pdf",
        source_format=SourceFormat.PDF,
        pages=tuple(
            PageText(number=number, text=text)
            for number, text in enumerate(pages, start=1)
        ),
        ocr_used=ocr_used,
    )


def test_page_mode_produces_one_record_per_page() -> None:
    result = parse_document_records(_document(FICHA, OUTRA), SourceSpec())

    assert result.record_count == 2
    assert result.columns == ("Código", "Nome", "CPF/CNPJ")
    assert result.records[0].values["Nome"] == "Ada Lovelace"
    assert result.records[1].values["Código"] == "ERP-2"


def test_page_mode_keeps_the_page_number_as_origin() -> None:
    """Uma rejeição precisa ser rastreável até a página do documento."""
    result = parse_document_records(_document(FICHA, OUTRA), SourceSpec())

    assert [record.row_number for record in result.records] == [1, 2]


def test_separator_mode_splits_a_continuous_report() -> None:
    text = f"RELATÓRIO\n-------\n{FICHA}-------\n{OUTRA}"
    document = DocumentText(
        source_name="relatorio.txt",
        source_format=SourceFormat.TXT,
        pages=(PageText(number=1, text=text),),
    )

    result = parse_document_records(
        document,
        SourceSpec(record_mode=RecordMode.SEPARATOR, record_separator=r"^-{3,}$"),
    )

    assert result.record_count == 2
    assert result.records[0].values["Nome"] == "Ada Lovelace"


def test_lines_without_a_label_are_ignored() -> None:
    """Cabeçalho e moldura de relatório não podem virar campo."""
    page = f"FICHA CADASTRAL DE CLIENTE\n=========\n{FICHA}"

    result = parse_document_records(_document(page), SourceSpec())

    assert result.columns == ("Código", "Nome", "CPF/CNPJ")


def test_empty_value_becomes_none() -> None:
    result = parse_document_records(
        _document("Nome: Ada\nTelefone:\n"), SourceSpec()
    )

    assert result.records[0].values["Telefone"] is None


def test_repeated_label_keeps_the_first_occurrence() -> None:
    """A repetição costuma ser rodapé ou moldura, não um segundo valor."""
    result = parse_document_records(
        _document("Nome: Ada\nNome: rodapé\n"), SourceSpec()
    )

    assert result.records[0].values["Nome"] == "Ada"


def test_page_without_labels_does_not_become_a_record() -> None:
    result = parse_document_records(_document("Capa do documento", FICHA), SourceSpec())

    assert result.record_count == 1
    assert result.records[0].row_number == 2


def test_document_without_any_label_fails_with_guidance() -> None:
    with pytest.raises(DocumentStructureError, match="Rótulo"):
        parse_document_records(_document("texto solto sem estrutura"), SourceSpec())


def test_separator_mode_requires_a_separator() -> None:
    with pytest.raises(DocumentStructureError, match="record_separator"):
        parse_document_records(
            _document(FICHA), SourceSpec(record_mode=RecordMode.SEPARATOR)
        )


def test_invalid_separator_regex_fails_with_a_clear_message() -> None:
    with pytest.raises(DocumentStructureError, match="express"):
        parse_document_records(
            _document(FICHA),
            SourceSpec(record_mode=RecordMode.SEPARATOR, record_separator="["),
        )


def test_ocr_result_carries_a_conference_warning() -> None:
    """Seção 12: resultado de OCR nunca é confiável sem validação."""
    result = parse_document_records(_document(FICHA, ocr_used=True), SourceSpec())

    assert result.ocr_used is True
    assert any("OCR" in warning for warning in result.warnings)


def test_custom_label_separator() -> None:
    result = parse_document_records(
        _document("Nome = Ada\nUF = SP\n"), SourceSpec(label_separator="=")
    )

    assert result.records[0].values["Nome"] == "Ada"
    assert result.records[0].values["UF"] == "SP"
