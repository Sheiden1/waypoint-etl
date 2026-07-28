"""Testes do extrator de planilhas Excel."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from openpyxl import Workbook

from waypoint_etl.application.dto.extraction import ExtractionOptions
from waypoint_etl.demo.synthetic import (
    CONTACTS_SHEET_NAME,
    CUSTOMERS_HEADER_ROW,
    CUSTOMERS_SHEET_NAME,
    write_legacy_xlsx,
)
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import (
    EmptySourceError,
    ExtractionError,
    SheetNotFoundError,
    SourceNotFoundError,
)
from waypoint_etl.infrastructure.extractors.excel_extractor import ExcelExtractor


@pytest.fixture
def extractor() -> ExcelExtractor:
    return ExcelExtractor()


def _write_workbook(path: Path, sheets: dict[str, list[list[object]]]) -> Path:
    workbook = Workbook()
    default_sheet = workbook.active
    if default_sheet is not None:
        workbook.remove(default_sheet)
    for name, rows in sheets.items():
        sheet = workbook.create_sheet(name)
        for row in rows:
            sheet.append(row)
    workbook.save(path)
    workbook.close()
    return path


def test_supports_xlsx_and_xlsm(extractor: ExcelExtractor) -> None:
    assert extractor.supports(Path("a.xlsx"))
    assert extractor.supports(Path("a.XLSM"))
    assert not extractor.supports(Path("a.csv"))


def test_reads_first_sheet_by_default(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx",
        {
            "Primeira": [["nome"], ["Ana"]],
            "Segunda": [["outro"], ["x"]],
        },
    )

    result = extractor.extract(source)

    assert result.source_format is SourceFormat.EXCEL
    assert result.sheet == "Primeira"
    assert result.available_sheets == ("Primeira", "Segunda")
    assert result.records[0].values == {"nome": "Ana"}
    assert result.records[0].sheet == "Primeira"
    assert result.records[0].row_number == 2


def test_reads_requested_sheet(extractor: ExcelExtractor, tmp_path: Path) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx",
        {"Clientes": [["nome"], ["Ana"]], "Contatos": [["contato"], ["Bruno"]]},
    )

    result = extractor.extract(source, ExtractionOptions(sheet="Contatos"))

    assert result.sheet == "Contatos"
    assert result.records[0].values == {"contato": "Bruno"}


def test_unknown_sheet_lists_available_ones(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(tmp_path / "a.xlsx", {"Clientes": [["nome"], ["Ana"]]})

    with pytest.raises(SheetNotFoundError, match="Clientes"):
        extractor.extract(source, ExtractionOptions(sheet="Faturas"))


def test_header_row_skips_title_rows(extractor: ExcelExtractor, tmp_path: Path) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx",
        {"Clientes": [["Relatório ERP"], ["nome", "cidade"], ["Ana", "Recife"]]},
    )

    result = extractor.extract(source, ExtractionOptions(header_row=2))

    assert result.columns == ("nome", "cidade")
    assert result.record_count == 1
    assert result.records[0].row_number == 3


def test_dates_and_numbers_become_stable_text(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx",
        {
            "Dados": [
                ["data", "codigo", "valor", "flag"],
                [dt.datetime(2024, 3, 15), 1000, 1234.5, True],
            ]
        },
    )

    result = extractor.extract(source)

    assert result.records[0].values == {
        "data": "2024-03-15",
        "codigo": "1000",
        "valor": "1234.5",
        "flag": "true",
    }


def test_blank_rows_are_skipped(extractor: ExcelExtractor, tmp_path: Path) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx",
        {"Dados": [["nome"], ["Ana"], [None], ["   "], ["Bruno"]]},
    )

    result = extractor.extract(source)

    assert [record.row_number for record in result.records] == [2, 5]


def test_duplicated_headers_are_renamed(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx", {"Dados": [["fone", "fone"], ["1", "2"]]}
    )

    result = extractor.extract(source)

    assert result.columns == ("fone", "fone (2)")
    assert result.warnings


def test_sheet_without_data_rows_returns_no_records(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(tmp_path / "a.xlsx", {"Dados": [["nome", "cidade"]]})

    result = extractor.extract(source)

    assert result.columns == ("nome", "cidade")
    assert result.records == ()


def test_blank_header_row_raises_empty_source(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(
        tmp_path / "a.xlsx", {"Dados": [[None, None], ["Ana", "Recife"]]}
    )

    with pytest.raises(EmptySourceError):
        extractor.extract(source)


def test_header_row_beyond_sheet_raises_empty_source(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(tmp_path / "a.xlsx", {"Dados": [["nome"], ["Ana"]]})

    with pytest.raises(EmptySourceError):
        extractor.extract(source, ExtractionOptions(header_row=9))


def test_invalid_header_row_raises_extraction_error(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = _write_workbook(tmp_path / "a.xlsx", {"Dados": [["nome"], ["Ana"]]})

    with pytest.raises(ExtractionError):
        extractor.extract(source, ExtractionOptions(header_row=0))


def test_non_excel_content_raises_extraction_error(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    source = tmp_path / "a.xlsx"
    source.write_text("isto não é uma planilha", encoding="utf-8")

    with pytest.raises(ExtractionError):
        extractor.extract(source)


def test_missing_file_raises_source_not_found(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    with pytest.raises(SourceNotFoundError):
        extractor.extract(tmp_path / "inexistente.xlsx")


def test_demo_workbook_has_two_sheets(
    extractor: ExcelExtractor, tmp_path: Path
) -> None:
    """A planilha de demonstração usa duas abas e cabeçalho na linha 2."""
    source = write_legacy_xlsx(tmp_path / "clientes_legado.xlsx")

    customers = extractor.extract(
        source, ExtractionOptions(header_row=CUSTOMERS_HEADER_ROW)
    )
    contacts = extractor.extract(source, ExtractionOptions(sheet=CONTACTS_SHEET_NAME))

    assert customers.sheet == CUSTOMERS_SHEET_NAME
    assert customers.available_sheets == (CUSTOMERS_SHEET_NAME, CONTACTS_SHEET_NAME)
    assert "CPF_CNPJ" in customers.columns
    assert customers.record_count >= 50
    assert "Nome Contato" in contacts.columns
    assert contacts.record_count >= 1
