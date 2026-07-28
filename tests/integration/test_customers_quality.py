"""Integração: qualidade sobre os dados sintéticos "sujos".

O gerador injeta de propósito 5 duplicatas, 5 documentos inválidos e 3 e-mails
inválidos (seção 22). Este teste confirma que o pipeline realmente os isola.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from waypoint_etl.demo.synthetic import write_legacy_xlsx
from waypoint_etl.infrastructure.extractors import get_tabular_extractor
from waypoint_etl.pipeline.deduplication import annotate_duplicates, find_duplicates
from waypoint_etl.pipeline.mappers import apply_mapping, load_mapping
from waypoint_etl.pipeline.validators import validate_records

pytestmark = pytest.mark.integration

TEMPLATE = Path("mappings/erp_legacy_customers.yaml")
REFERENCE = date(2030, 1, 1)


@pytest.fixture
def validated(tmp_path: Path):  # type: ignore[no-untyped-def]
    """Executa o pipeline até a validação sobre a planilha de demonstração."""
    workbook = write_legacy_xlsx(tmp_path / "clientes_legado.xlsx")
    template = load_mapping(TEMPLATE)
    extractor = get_tabular_extractor(workbook)

    extraction = extractor.extract(workbook, template.source.to_extraction_options())
    mapped = apply_mapping(extraction, template)
    return validate_records(mapped.records, template.entity, reference_date=REFERENCE)


def test_batch_is_split_into_valid_and_rejected(validated) -> None:  # type: ignore[no-untyped-def]
    valid = [record for record in validated if record.is_valid]
    rejected = [record for record in validated if not record.is_valid]

    assert valid, "o lote deve produzir registros válidos"
    assert rejected, "os documentos inválidos injetados devem ser rejeitados"
    assert len(valid) + len(rejected) == len(validated)


def test_injected_invalid_documents_are_rejected(validated) -> None:  # type: ignore[no-untyped-def]
    """O gerador corrompe 5 documentos com 111.111.111-11."""
    rejected = [
        record
        for record in validated
        if any(issue.code == "invalid_document" for issue in record.errors)
    ]

    assert len(rejected) >= 5


def test_injected_invalid_emails_are_rejected(validated) -> None:  # type: ignore[no-untyped-def]
    rejected = [
        record
        for record in validated
        if any(issue.code == "invalid_email" for issue in record.errors)
    ]

    assert len(rejected) >= 3


def test_rejected_records_carry_the_source_row_number(validated) -> None:  # type: ignore[no-untyped-def]
    """Rastreabilidade: cada rejeição aponta para a linha de origem."""
    rejected = [record for record in validated if not record.is_valid]

    assert all(record.row_number > 2 for record in rejected)
    assert len({record.row_number for record in rejected}) == len(rejected)


def test_injected_duplicates_are_detected(validated) -> None:  # type: ignore[no-untyped-def]
    """O gerador acrescenta 5 duplicatas com o mesmo documento."""
    result = find_duplicates(validated)

    assert len(result.exact) >= 4
    assert all(
        match.key in {"document", "email", "external_id"} for match in result.exact
    )


def test_duplicates_are_flagged_but_never_removed(validated) -> None:  # type: ignore[no-untyped-def]
    result = find_duplicates(validated)
    annotated = annotate_duplicates(validated, result)

    duplicated = [
        record
        for record in annotated
        if any(issue.code.startswith("duplicate_") for issue in record.warnings)
    ]

    assert duplicated
    assert all(record.is_valid for record in duplicated)
    assert len(annotated) == len(validated)


def test_valid_records_have_normalized_documents(validated) -> None:  # type: ignore[no-untyped-def]
    valid = [record for record in validated if record.is_valid]

    for record in valid:
        assert record.entity is not None
        assert record.entity.document.isdigit()
        assert len(record.entity.document) in (11, 14)


def test_no_full_document_appears_in_displayed_issues(validated) -> None:  # type: ignore[no-untyped-def]
    """Seção 18: auditoria apresentada nunca mostra o documento inteiro."""
    for record in validated:
        for issue in record.issues_for_display():
            if issue.field == "document" and issue.original_value:
                assert "*" in issue.original_value
