"""Testes da aplicação do template De/Para e do catálogo de transformações."""

from __future__ import annotations

from textwrap import dedent

import pytest

from waypoint_etl.application.dto.extraction import ExtractionResult, SourceRecord
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.pipeline.mappers.loader import MappingError, parse_mapping
from waypoint_etl.pipeline.mappers.mapper import apply_mapping, map_record
from waypoint_etl.pipeline.mappers.transforms import (
    apply_transforms,
    available_transforms,
    is_known_transform,
)

TEMPLATE = parse_mapping(
    dedent(
        """
        version: 1
        name: Teste
        entity: customers
        fields:
          Nome Cliente:
            target: full_name
            required: true
            transforms: [clean_text, title_case]
          CPF_CNPJ:
            target: document
            required: true
            transforms: [digits_only]
          Fone:
            target: phone
            transforms: [brazilian_phone]
        ignored_fields:
          - Observacao
        """
    )
)


def _extraction(*rows: dict[str, str | None], columns: tuple[str, ...]) -> (
    ExtractionResult
):
    return ExtractionResult(
        source_name="clientes.csv",
        source_format=SourceFormat.CSV,
        columns=columns,
        records=tuple(
            SourceRecord(row_number=index, values=row)
            for index, row in enumerate(rows, start=2)
        ),
    )


def test_maps_source_columns_to_canonical_fields() -> None:
    record = SourceRecord(
        row_number=2,
        values={
            "Nome Cliente": "  MARIA DA SILVA  ",
            "CPF_CNPJ": "390.533.447-05",
            "Fone": "+55 (11) 98765-4321",
        },
    )

    mapped = map_record(record, TEMPLATE)

    assert mapped.values == {
        "full_name": "Maria da Silva",
        "document": "39053344705",
        "phone": "11987654321",
    }
    assert mapped.row_number == 2


def test_records_which_transforms_changed_the_value() -> None:
    """O relatório de auditoria precisa mostrar as correções automáticas."""
    record = SourceRecord(
        row_number=2,
        values={"Nome Cliente": "  ANA  ", "CPF_CNPJ": "39053344705", "Fone": None},
    )

    mapped = map_record(record, TEMPLATE)

    assert "title_case" in mapped.applied_transforms
    # O documento já vinha só com dígitos: nada mudou por causa dele.
    assert mapped.values["document"] == "39053344705"


def test_missing_source_value_becomes_none() -> None:
    record = SourceRecord(row_number=2, values={"Nome Cliente": "Ana"})

    mapped = map_record(record, TEMPLATE)

    assert mapped.values["document"] is None
    assert mapped.values["phone"] is None


def test_default_fills_only_when_value_is_absent() -> None:
    template = parse_mapping(
        dedent(
            """
            version: 1
            name: T
            entity: customers
            fields:
              Nome: {target: full_name}
              CPF: {target: document}
              UF: {target: state, default: SP, transforms: [uf]}
            """
        )
    )

    filled = map_record(SourceRecord(2, {"UF": "rj"}), template)
    defaulted = map_record(SourceRecord(3, {"UF": "N/A"}), template)

    assert filled.values["state"] == "RJ"
    assert defaulted.values["state"] == "SP"


def test_apply_mapping_over_a_batch() -> None:
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "390.533.447-05", "Fone": "11987654321"},
        {"Nome Cliente": "bruno", "CPF_CNPJ": "11222333000181", "Fone": None},
        columns=("Nome Cliente", "CPF_CNPJ", "Fone"),
    )

    result = apply_mapping(extraction, TEMPLATE)

    assert result.record_count == 2
    assert result.template_name == "Teste"
    assert result.records[0].values["full_name"] == "Ana"
    assert result.records[1].values["document"] == "11222333000181"


def test_missing_required_column_fails_before_processing_any_row() -> None:
    """Template incompatível é erro de configuração, não lote rejeitado."""
    extraction = _extraction({"Nome Cliente": "ana"}, columns=("Nome Cliente", "Fone"))

    with pytest.raises(MappingError, match="CPF_CNPJ"):
        apply_mapping(extraction, TEMPLATE)


def test_missing_optional_column_runs_with_a_warning() -> None:
    """Export legado sem uma coluna opcional não deve travar a migração."""
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "1"},
        columns=("Nome Cliente", "CPF_CNPJ"),
    )

    result = apply_mapping(extraction, TEMPLATE)

    assert result.records[0].values["phone"] is None
    assert any("opcional(is) ausente(s)" in warning for warning in result.warnings)
    assert any("Fone" in warning for warning in result.warnings)


def test_missing_optional_column_with_default_uses_the_default() -> None:
    """O padrão declarado vale também quando a coluna inteira falta."""
    template = parse_mapping(
        dedent(
            """
            version: 1
            name: Teste
            entity: customers
            fields:
              Nome Cliente:
                target: full_name
                required: true
              CPF_CNPJ:
                target: document
                required: true
              UF:
                target: state
                default: SP
            """
        )
    )
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "1"},
        columns=("Nome Cliente", "CPF_CNPJ"),
    )

    result = apply_mapping(extraction, template)

    assert result.records[0].values["state"] == "SP"
    assert any("opcional(is) ausente(s)" in warning for warning in result.warnings)


def test_template_can_require_a_canonically_optional_column() -> None:
    """O flag required do YAML bloqueia mesmo fora do schema canônico."""
    template = parse_mapping(
        dedent(
            """
            version: 1
            name: Teste
            entity: customers
            fields:
              Nome Cliente:
                target: full_name
                required: true
              CPF_CNPJ:
                target: document
                required: true
              Correio:
                target: email
                required: true
            """
        )
    )
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "1"},
        columns=("Nome Cliente", "CPF_CNPJ"),
    )

    with pytest.raises(MappingError, match="Correio"):
        apply_mapping(extraction, template)


def test_unmapped_column_produces_a_warning() -> None:
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "1", "Fone": "1", "Extra": "x"},
        columns=("Nome Cliente", "CPF_CNPJ", "Fone", "Extra"),
    )

    result = apply_mapping(extraction, TEMPLATE)

    assert result.unmapped_columns == ("Extra",)
    assert any("não mapeada" in warning for warning in result.warnings)


def test_explicitly_ignored_column_produces_no_warning() -> None:
    extraction = _extraction(
        {"Nome Cliente": "ana", "CPF_CNPJ": "1", "Fone": "1", "Observacao": "x"},
        columns=("Nome Cliente", "CPF_CNPJ", "Fone", "Observacao"),
    )

    result = apply_mapping(extraction, TEMPLATE)

    assert result.unmapped_columns == ()
    assert result.warnings == ()


# --- Catálogo de transformações ----------------------------------------------


def test_transforms_are_applied_in_declared_order() -> None:
    assert apply_transforms("  ana maria  ", ("clean_text", "title_case")) == (
        "Ana Maria"
    )
    assert apply_transforms("ANA", ("lowercase", "title_case")) == "Ana"


def test_typed_transforms_are_skipped_at_mapping_time() -> None:
    """``brazilian_date`` converte tipo: roda na validação, não aqui."""
    assert apply_transforms("15/03/2024", ("brazilian_date",)) == "15/03/2024"


def test_catalog_is_closed() -> None:
    assert is_known_transform("digits_only")
    assert is_known_transform("brazilian_date")
    assert not is_known_transform("os.system")
    assert "title_case" in available_transforms()
