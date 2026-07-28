"""Testes do extrator CSV."""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.application.dto.extraction import ExtractionOptions
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.domain.errors import (
    EmptySourceError,
    ExtractionError,
    SourceNotFoundError,
)
from waypoint_etl.infrastructure.extractors.csv_extractor import CsvExtractor


@pytest.fixture
def extractor() -> CsvExtractor:
    return CsvExtractor()


def _write(path: Path, content: str, *, encoding: str = "utf-8") -> Path:
    path.write_text(content, encoding=encoding)
    return path


def test_supports_only_csv(extractor: CsvExtractor) -> None:
    assert extractor.supports(Path("a.csv"))
    assert extractor.supports(Path("A.CSV"))
    assert not extractor.supports(Path("a.xlsx"))


def test_extracts_rows_with_header(extractor: CsvExtractor, tmp_path: Path) -> None:
    source = _write(
        tmp_path / "clientes.csv",
        "Código,Nome Cliente\nERP-1,Ana Silva\nERP-2,Bruno Souza\n",
    )

    result = extractor.extract(source)

    assert result.source_format is SourceFormat.CSV
    assert result.source_name == "clientes.csv"
    assert result.columns == ("Código", "Nome Cliente")
    assert result.record_count == 2
    assert result.records[0].values == {"Código": "ERP-1", "Nome Cliente": "Ana Silva"}
    assert result.records[0].row_number == 2
    assert result.records[1].row_number == 3


def test_empty_and_whitespace_cells_become_none(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome,fone\nAna,   \n")

    result = extractor.extract(source)

    assert result.records[0].values == {"nome": "Ana", "fone": None}


def test_blank_lines_are_skipped_but_numbering_is_preserved(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nAna\n\n\nBruno\n")

    result = extractor.extract(source)

    assert [record.row_number for record in result.records] == [2, 5]


def test_short_and_long_rows_do_not_break_the_batch(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "a,b,c\n1,2\n1,2,3,4\n")

    result = extractor.extract(source)

    assert result.records[0].values == {"a": "1", "b": "2", "c": None}
    assert result.records[1].values == {"a": "1", "b": "2", "c": "3"}


def test_semicolon_delimiter_is_detected(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome;cidade\nAna;São Paulo\n")

    result = extractor.extract(source)

    assert result.columns == ("nome", "cidade")
    assert result.records[0].values["cidade"] == "São Paulo"


def test_explicit_delimiter_overrides_detection(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome|cidade\nAna|Recife\n")

    result = extractor.extract(source, ExtractionOptions(delimiter="|"))

    assert result.columns == ("nome", "cidade")


def test_quoted_field_with_newline_keeps_row_numbering(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    content = 'nome,obs\n"Ana","linha 1\nlinha 2"\nBruno,ok\n'
    source = _write(tmp_path / "a.csv", content)

    result = extractor.extract(source)

    assert result.records[0].values["obs"] == "linha 1\nlinha 2"
    assert result.records[1].values["nome"] == "Bruno"


def test_header_row_skips_title_lines(extractor: CsvExtractor, tmp_path: Path) -> None:
    source = _write(tmp_path / "a.csv", "Relatório ERP\nnome,cidade\nAna,Recife\n")

    result = extractor.extract(source, ExtractionOptions(header_row=2))

    assert result.columns == ("nome", "cidade")
    assert result.record_count == 1


def test_duplicated_headers_are_renamed_with_warning(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "fone,fone\n1111,2222\n")

    result = extractor.extract(source)

    assert result.columns == ("fone", "fone (2)")
    assert any("duplicado" in warning for warning in result.warnings)


def test_missing_header_name_gets_positional_name(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome,\nAna,x\n")

    result = extractor.extract(source)

    assert result.columns == ("nome", "coluna_2")
    assert any("sem cabeçalho" in warning for warning in result.warnings)


def test_cp1252_file_is_read_with_warning(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nJoão Ação\n", encoding="cp1252")

    result = extractor.extract(source)

    assert result.records[0].values["nome"] == "João Ação"
    assert any("codificação" in warning for warning in result.warnings)


def test_utf8_bom_is_stripped_from_header(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nAna\n", encoding="utf-8-sig")

    result = extractor.extract(source)

    assert result.columns == ("nome",)
    assert result.warnings == ()


def test_missing_file_raises_source_not_found(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    with pytest.raises(SourceNotFoundError):
        extractor.extract(tmp_path / "inexistente.csv")


def test_directory_raises_source_not_found(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    with pytest.raises(SourceNotFoundError):
        extractor.extract(tmp_path)


def test_empty_file_raises_empty_source(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    with pytest.raises(EmptySourceError):
        extractor.extract(_write(tmp_path / "a.csv", ""))


def test_header_row_beyond_end_of_file_raises_empty_source(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nAna\n")

    with pytest.raises(EmptySourceError):
        extractor.extract(source, ExtractionOptions(header_row=9))


def test_invalid_header_row_raises_extraction_error(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nAna\n")

    with pytest.raises(ExtractionError):
        extractor.extract(source, ExtractionOptions(header_row=0))


def test_unknown_encoding_raises_extraction_error(
    extractor: CsvExtractor, tmp_path: Path
) -> None:
    source = _write(tmp_path / "a.csv", "nome\nAna\n")

    with pytest.raises(ExtractionError, match="Codificação desconhecida"):
        extractor.extract(source, ExtractionOptions(encoding="nao-existe"))


def test_demo_csv_sample_is_readable(extractor: CsvExtractor) -> None:
    """O fixture versionado em ``samples/input`` deve continuar legível."""
    sample = Path("samples/input/clientes_legado.csv")
    if not sample.exists():  # pragma: no cover - fixture opcional no ambiente
        pytest.skip("fixture de demonstração ausente")

    result = extractor.extract(sample)

    assert "CPF_CNPJ" in result.columns
    assert result.record_count >= 50
