"""Testes dos contratos de extração de documentos."""

from __future__ import annotations

from waypoint_etl.application.dto.document import DocumentText, PageText
from waypoint_etl.domain.enums.source_format import SourceFormat


def _document(*texts: str) -> DocumentText:
    return DocumentText(
        source_name="a.pdf",
        source_format=SourceFormat.PDF,
        pages=tuple(
            PageText(number=number, text=text)
            for number, text in enumerate(texts, start=1)
        ),
    )


def test_page_counts_ignore_surrounding_whitespace() -> None:
    page = PageText(number=1, text="  Ana  ")

    assert page.character_count == 3
    assert not page.is_empty


def test_blank_page_is_empty() -> None:
    assert PageText(number=1, text="   \n ").is_empty


def test_text_joins_pages_and_drops_empty_ones() -> None:
    document = _document("primeira", "   ", "terceira")

    assert document.text == "primeira\n\nterceira"
    assert document.page_count == 3
    assert document.empty_pages == (2,)


def test_character_count_sums_pages() -> None:
    assert _document("abc", "de").character_count == 5


def test_document_without_text_is_empty() -> None:
    document = _document("", "  ")

    assert document.is_empty
    assert document.text == ""
    assert document.empty_pages == (1, 2)


def test_document_defaults_to_no_ocr() -> None:
    document = _document("abc")

    assert document.ocr_used is False
    assert document.warnings == ()
