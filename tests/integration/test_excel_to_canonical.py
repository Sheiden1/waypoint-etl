"""Integração: planilha legada -> extração -> De/Para -> registros canônicos.

Cobre o caminho declarado na seção 19 ("Excel para registros canônicos") usando
o template versionado em ``mappings/`` e o gerador de dados sintéticos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.demo.synthetic import write_legacy_xlsx
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.infrastructure.extractors import get_tabular_extractor
from waypoint_etl.pipeline.mappers import apply_mapping, load_mapping

pytestmark = pytest.mark.integration

CUSTOMERS_TEMPLATE = Path("mappings/erp_legacy_customers.yaml")
CONTACTS_TEMPLATE = Path("mappings/erp_legacy_contacts.yaml")


@pytest.fixture
def workbook(tmp_path: Path) -> Path:
    return write_legacy_xlsx(tmp_path / "clientes_legado.xlsx")


def test_customers_sheet_becomes_canonical_records(workbook: Path) -> None:
    template = load_mapping(CUSTOMERS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    assert template.entity is EntityType.CUSTOMERS
    assert result.record_count >= 50

    first = result.records[0]
    assert set(first.values) == {
        "external_id",
        "full_name",
        "document",
        "email",
        "phone",
        "postal_code",
        "city",
        "state",
        "created_at",
    }


def test_values_arrive_normalized(workbook: Path) -> None:
    template = load_mapping(CUSTOMERS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    documents = [r.values["document"] for r in result.records if r.values["document"]]
    phones = [r.values["phone"] for r in result.records if r.values["phone"]]
    states = [r.values["state"] for r in result.records if r.values["state"]]

    assert all(value.isdigit() for value in documents), (
        "documento deve ficar sem máscara"
    )
    assert all(value.isdigit() for value in phones), "telefone deve ficar sem máscara"
    assert all(value.isupper() and len(value) == 2 for value in states)


def test_dirty_names_are_cleaned(workbook: Path) -> None:
    """O gerador injeta nomes em caixa alta com espaços extras."""
    template = load_mapping(CUSTOMERS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    names = [r.values["full_name"] for r in result.records if r.values["full_name"]]

    assert names
    assert all(name == name.strip() for name in names)
    assert all("  " not in name for name in names)
    assert not any(name.isupper() for name in names if len(name) > 3)


def test_null_markers_become_none(workbook: Path) -> None:
    """O gerador injeta "-" e "N/A" em telefones; devem virar ausência."""
    template = load_mapping(CUSTOMERS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    phones = [r.values["phone"] for r in result.records]

    assert None in phones
    assert "-" not in phones
    assert "N/A" not in phones


def test_ignored_column_is_not_carried_over(workbook: Path) -> None:
    template = load_mapping(CUSTOMERS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    assert "Observação Interna Antiga" in extraction.columns
    assert result.unmapped_columns == ()
    assert result.warnings == ()


def test_contacts_sheet_uses_its_own_template(workbook: Path) -> None:
    template = load_mapping(CONTACTS_TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    result = apply_mapping(extraction, template)

    assert template.entity is EntityType.CONTACTS
    assert result.record_count >= 1
    assert result.records[0].values["customer_document"]
    assert result.records[0].values["name"]
