"""Integração: documento legado -> extração -> estruturação -> canônico.

Fecha a lacuna que a seção 19 declarava pendente: documentos eram apenas
inspecionados e não viravam registros canônicos. O caminho usa o template
versionado em ``mappings/`` e o gerador de dados sintéticos.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.application.use_cases.run_migration import (
    MigrationRequest,
    run_migration,
)
from waypoint_etl.demo.document_files import (
    write_customer_form_docx,
    write_customers_txt,
)
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.infrastructure.extractors import get_document_extractor
from waypoint_etl.pipeline.documents import parse_document_records
from waypoint_etl.pipeline.mappers import apply_mapping, load_mapping

pytestmark = pytest.mark.integration

TXT_TEMPLATE = Path("mappings/erp_legacy_customers_txt.yaml")
DOCX_TEMPLATE = Path("mappings/erp_legacy_customers_docx.yaml")


@pytest.fixture
def report(tmp_path: Path) -> Path:
    return write_customers_txt(tmp_path / "clientes_legado.txt")


def test_txt_report_becomes_canonical_records(report: Path) -> None:
    template = load_mapping(TXT_TEMPLATE)
    extractor = get_document_extractor(report)

    document = extractor.extract_text(report, template.source.to_extraction_options())
    extraction = parse_document_records(document, template.source)
    result = apply_mapping(extraction, template)

    assert template.entity is EntityType.CUSTOMERS
    assert result.record_count == 10

    first = result.records[0].values
    assert first["full_name"] == "Almeida S/A"
    assert first["document"] == "98949230000104"
    assert first["state"] == "AM"


def test_txt_report_runs_the_whole_pipeline(report: Path, tmp_path: Path) -> None:
    """Documento produz os quatro artefatos, como qualquer outra origem."""
    result = run_migration(
        MigrationRequest(
            source=report,
            mapping=TXT_TEMPLATE,
            output_dir=tmp_path / "exports",
            dry_run=True,
        )
    )

    assert result.total_records == 10
    # A fixture sintética carrega cinco documentos e três e-mails inválidos.
    assert len(result.rejected) == 7
    assert {file.name for file in result.exported_files} == {
        "accepted.csv",
        "rejected.xlsx",
        "duplicates.csv",
        "audit-report.json",
    }


def test_docx_form_uses_its_own_label_separator(tmp_path: Path) -> None:
    """A mesma informação muda de forma conforme o formato de origem.

    O extrator de DOCX representa linha de tabela como ``Rótulo | valor``,
    então o template declara ``|`` onde o relatório TXT declara ``:``.
    """
    form = write_customer_form_docx(tmp_path / "ficha.docx")
    template = load_mapping(DOCX_TEMPLATE)
    extractor = get_document_extractor(form)

    document = extractor.extract_text(form, None)
    extraction = parse_document_records(document, template.source)
    result = apply_mapping(extraction, template)

    assert result.record_count >= 1
    assert result.records[0].values["full_name"] == "Almeida S/A"
