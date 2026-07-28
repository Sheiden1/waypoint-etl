"""Testes do carregamento e validação do template De/Para."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.pipeline.mappers.loader import (
    MappingError,
    load_mapping,
    parse_mapping,
)

MINIMAL = dedent(
    """
    version: 1
    name: Teste
    entity: customers
    fields:
      Nome:
        target: full_name
        required: true
      CPF:
        target: document
        transforms:
          - digits_only
    """
)


def test_parses_a_minimal_template() -> None:
    template = parse_mapping(MINIMAL)

    assert template.name == "Teste"
    assert template.entity is EntityType.CUSTOMERS
    assert template.version == 1
    assert template.source_columns == ("Nome", "CPF")
    assert template.target_fields == ("full_name", "document")


def test_parses_the_source_block() -> None:
    template = parse_mapping(
        dedent(
            """
            version: 1
            name: Teste
            entity: customers
            source:
              type: excel
              sheet: Clientes
              header_row: 2
            fields:
              Nome: {target: full_name}
              CPF: {target: document}
            """
        )
    )

    assert template.source.type is SourceFormat.EXCEL
    assert template.source.sheet == "Clientes"
    assert template.source.header_row == 2


def test_source_block_becomes_extraction_options() -> None:
    """O template é quem passa a preencher as opções do extrator."""
    template = parse_mapping(
        dedent(
            """
            version: 1
            name: Teste
            entity: customers
            source: {sheet: Clientes, header_row: 2, delimiter: ";"}
            fields:
              Nome: {target: full_name}
              CPF: {target: document}
            """
        )
    )

    options = template.source.to_extraction_options()

    assert options.sheet == "Clientes"
    assert options.header_row == 2
    assert options.delimiter == ";"


def test_source_block_is_optional() -> None:
    template = parse_mapping(MINIMAL)

    assert template.source.sheet is None
    assert template.source.header_row == 1


# --- Erros exigidos pela seção 10 --------------------------------------------


def test_invalid_yaml_reports_the_line() -> None:
    broken = "name: Teste\n  entity: customers\n"

    with pytest.raises(MappingError, match="não é um YAML válido"):
        parse_mapping(broken)


def test_two_columns_pointing_to_the_same_target_is_rejected() -> None:
    duplicated = dedent(
        """
        version: 1
        name: Teste
        entity: customers
        fields:
          Nome: {target: full_name}
          Razao Social: {target: full_name}
          CPF: {target: document}
        """
    )

    with pytest.raises(MappingError, match="mesmo campo 'full_name'"):
        parse_mapping(duplicated)


def test_missing_required_canonical_field_is_rejected() -> None:
    without_document = dedent(
        """
        version: 1
        name: Teste
        entity: customers
        fields:
          Nome: {target: full_name}
        """
    )

    with pytest.raises(MappingError, match=r"obrigatório.*document"):
        parse_mapping(without_document)


def test_unknown_transform_lists_the_available_ones() -> None:
    unknown = dedent(
        """
        version: 1
        name: Teste
        entity: customers
        fields:
          Nome:
            target: full_name
            transforms: [inventada]
          CPF: {target: document}
        """
    )

    with pytest.raises(MappingError, match="Transformação desconhecida"):
        parse_mapping(unknown)


def test_unknown_target_field_is_rejected() -> None:
    unknown_target = dedent(
        """
        version: 1
        name: Teste
        entity: customers
        fields:
          Nome: {target: full_name}
          CPF: {target: document}
          Extra: {target: campo_inexistente}
        """
    )

    with pytest.raises(MappingError, match="não existe no schema"):
        parse_mapping(unknown_target)


# --- Demais validações estruturais -------------------------------------------


def test_unknown_entity_lists_the_options() -> None:
    with pytest.raises(MappingError, match="Entidade desconhecida"):
        parse_mapping("version: 1\nname: T\nentity: pedidos\nfields: {}\n")


def test_unsupported_version_is_rejected() -> None:
    with pytest.raises(MappingError, match="Versão de template não suportada"):
        parse_mapping(MINIMAL.replace("version: 1", "version: 2"))


def test_empty_template_is_rejected() -> None:
    with pytest.raises(MappingError, match="está vazio"):
        parse_mapping("")


def test_template_that_is_not_a_mapping_is_rejected() -> None:
    with pytest.raises(MappingError, match="mapeamento de chaves"):
        parse_mapping("- um\n- dois\n")


def test_missing_name_is_rejected() -> None:
    with pytest.raises(MappingError, match="campo 'name'"):
        parse_mapping("version: 1\nentity: customers\nfields: {}\n")


def test_fields_block_is_required() -> None:
    with pytest.raises(MappingError, match="bloco 'fields'"):
        parse_mapping("version: 1\nname: T\nentity: customers\n")


def test_column_without_target_is_rejected() -> None:
    without_target = dedent(
        """
        version: 1
        name: T
        entity: customers
        fields:
          Nome: {required: true}
        """
    )

    with pytest.raises(MappingError, match="está sem 'target'"):
        parse_mapping(without_target)


def test_column_defined_as_scalar_is_rejected() -> None:
    with pytest.raises(MappingError, match="deve declarar ao menos 'target'"):
        parse_mapping(
            "version: 1\nname: T\nentity: customers\nfields:\n  Nome: full_name\n"
        )


@pytest.mark.parametrize("header_row", ["0", "-1", "abc"])
def test_invalid_header_row_is_rejected(header_row: str) -> None:
    template = dedent(
        f"""
        version: 1
        name: T
        entity: customers
        source: {{header_row: {header_row}}}
        fields:
          Nome: {{target: full_name}}
          CPF: {{target: document}}
        """
    )

    with pytest.raises(MappingError, match="header_row"):
        parse_mapping(template)


def test_unknown_source_type_is_rejected() -> None:
    template = MINIMAL.replace(
        "entity: customers", "entity: customers\nsource:\n  type: xls"
    )

    with pytest.raises(MappingError, match="Formato de origem desconhecido"):
        parse_mapping(template)


def test_transforms_must_be_a_list() -> None:
    template = dedent(
        """
        version: 1
        name: T
        entity: customers
        fields:
          Nome:
            target: full_name
            transforms: strip
          CPF: {target: document}
        """
    )

    with pytest.raises(MappingError, match="deve ser uma lista"):
        parse_mapping(template)


# --- Leitura de arquivo -------------------------------------------------------


def test_load_mapping_reads_from_disk(tmp_path: Path) -> None:
    path = tmp_path / "template.yaml"
    path.write_text(MINIMAL, encoding="utf-8")

    template = load_mapping(path)

    assert template.name == "Teste"


def test_load_mapping_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(MappingError, match="não encontrado"):
        load_mapping(tmp_path / "inexistente.yaml")


@pytest.mark.parametrize(
    "filename",
    [
        "erp_legacy_customers.yaml",
        "erp_legacy_contacts.yaml",
        "erp_legacy_invoices.yaml",
    ],
)
def test_shipped_templates_are_valid(filename: str) -> None:
    """Os templates versionados no repositório precisam carregar."""
    path = Path("mappings") / filename
    if not path.exists():  # pragma: no cover - ambiente sem os templates
        pytest.skip("templates não disponíveis")

    template = load_mapping(path)

    assert template.fields
    assert template.entity in EntityType
