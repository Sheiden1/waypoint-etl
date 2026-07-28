"""Testes dos adaptadores da interface Streamlit."""

from __future__ import annotations

from pathlib import Path

import pytest

from support.ocr import FakeOcrEngine
from waypoint_etl.application.dto.extraction import ExtractionOptions
from waypoint_etl.demo.synthetic import write_customers_csv
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.enums.source_format import SourceFormat
from waypoint_etl.pipeline.mappers.loader import MappingError, parse_mapping
from waypoint_etl.presentation.streamlit.workflow import (
    MappingSource,
    build_mapping_yaml,
    inspect_uploaded_source,
    run_uploaded_migration,
    safe_upload_name,
    upload_digest,
)

CUSTOMERS_CSV_TEMPLATE = Path("mappings/erp_legacy_customers_csv.yaml")


def test_safe_upload_name_prevents_path_traversal() -> None:
    assert safe_upload_name("../../segredo/clientes.csv") == "clientes.csv"
    assert safe_upload_name(r"..\..\segredo\clientes.csv") == "clientes.csv"


def test_mapping_source_requires_exactly_one_origin() -> None:
    with pytest.raises(ValueError, match="exatamente um"):
        MappingSource(name="mapping.yaml")

    with pytest.raises(ValueError, match="exatamente um"):
        MappingSource(name="mapping.yaml", path=Path("x"), content=b"x")


def test_upload_digest_changes_with_name_or_content() -> None:
    first = upload_digest("clientes.csv", b"a")

    assert first != upload_digest("contatos.csv", b"a")
    assert first != upload_digest("clientes.csv", b"b")


def test_inspect_upload_uses_the_shared_use_case(tmp_path: Path) -> None:
    source = write_customers_csv(tmp_path / "clientes.csv", count=3)

    preview = inspect_uploaded_source(
        source.name,
        source.read_bytes(),
        options=ExtractionOptions(header_row=1),
    )

    assert preview.is_tabular is True
    assert preview.source_format is SourceFormat.CSV
    assert "CPF_CNPJ" in preview.columns
    assert len(preview.rows) >= 3


def test_inspect_image_wires_the_ocr_engine(tmp_path: Path) -> None:
    from waypoint_etl.demo.document_files import write_scanned_form_image

    source = write_scanned_form_image(tmp_path / "ficha.png")

    preview = inspect_uploaded_source(
        source.name,
        source.read_bytes(),
        ocr_engine=FakeOcrEngine(text="FICHA CADASTRAL"),
    )

    assert preview.ocr_used is True
    assert preview.text_preview == "FICHA CADASTRAL"


def test_visual_mapping_builder_produces_a_valid_template() -> None:
    content = build_mapping_yaml(
        name="Clientes visual",
        entity=EntityType.CUSTOMERS,
        source_format=SourceFormat.CSV,
        assignments={
            "Nome": "full_name",
            "CPF/CNPJ": "document",
            "Notas": None,
        },
    )

    template = parse_mapping(content.decode("utf-8"), source_name="visual.yaml")

    assert template.name == "Clientes visual"
    assert template.source.type is SourceFormat.CSV
    assert template.mapping_for_target("document") is not None
    assert template.mapping_for_target("document").transforms == ("digits_only",)
    assert template.ignored_fields == ("Notas",)


def test_visual_mapping_builder_requires_the_canonical_fields() -> None:
    with pytest.raises(MappingError, match="full_name"):
        build_mapping_yaml(
            name="Incompleto",
            entity=EntityType.CUSTOMERS,
            source_format=SourceFormat.CSV,
            assignments={"CPF/CNPJ": "document"},
        )


def test_uploaded_migration_runs_the_same_pipeline_as_cli(tmp_path: Path) -> None:
    source = write_customers_csv(tmp_path / "clientes.csv", count=8)
    output = tmp_path / "exports"

    result = run_uploaded_migration(
        source_name="../../clientes.csv",
        source_content=source.read_bytes(),
        mapping=MappingSource(
            name=CUSTOMERS_CSV_TEMPLATE.name,
            path=CUSTOMERS_CSV_TEMPLATE,
        ),
        output_dir=output,
        entity=EntityType.CUSTOMERS,
    )

    assert result.run.dry_run is True
    assert result.run.source_filename == "clientes.csv"
    assert result.total_records >= 8
    assert {path.name for path in result.exported_files} == {
        "accepted.csv",
        "rejected.xlsx",
        "duplicates.csv",
        "audit-report.json",
    }


def test_uploaded_yaml_can_drive_the_migration(tmp_path: Path) -> None:
    source = write_customers_csv(tmp_path / "clientes.csv", count=4)

    result = run_uploaded_migration(
        source_name=source.name,
        source_content=source.read_bytes(),
        mapping=MappingSource(
            name="custom.yaml",
            content=CUSTOMERS_CSV_TEMPLATE.read_bytes(),
        ),
        output_dir=tmp_path / "exports",
        entity=EntityType.CUSTOMERS,
    )

    assert result.total_records >= 4
    assert result.run.mapping_name == "ERP Legado - Clientes (CSV)"
