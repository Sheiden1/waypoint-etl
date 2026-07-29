"""Integração da CLI: ``inspect`` e ``migrate`` de ponta a ponta.

Cobre o caminho completo declarado na seção 19 ("pipeline completo em
``dry-run``" e "geração dos quatro arquivos de saída").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from waypoint_etl.demo.synthetic import write_customers_csv, write_legacy_xlsx
from waypoint_etl.infrastructure.reports.exporters import (
    ACCEPTED_FILENAME,
    DUPLICATES_FILENAME,
    REJECTED_FILENAME,
)
from waypoint_etl.presentation.cli.main import app

pytestmark = pytest.mark.integration

runner = CliRunner()

CUSTOMERS_TEMPLATE = "mappings/erp_legacy_customers.yaml"
CUSTOMERS_CSV_TEMPLATE = "mappings/erp_legacy_customers_csv.yaml"
AUDIT_FILENAME = "audit-report.json"


@pytest.fixture
def workbook(tmp_path: Path) -> Path:
    return write_legacy_xlsx(tmp_path / "clientes_legado.xlsx")


def _migrate(source: Path, output: Path, *extra: str):  # type: ignore[no-untyped-def]
    return runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(source),
            "--mapping",
            CUSTOMERS_TEMPLATE,
            "--output",
            str(output),
            *extra,
        ],
    )


# --- version / inspect --------------------------------------------------------


def test_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "Waypoint" in result.stdout


def test_inspect_tabular_lists_columns_and_sheets(workbook: Path) -> None:
    result = runner.invoke(
        app, ["inspect", str(workbook), "--sheet", "Clientes", "--header-row", "2"]
    )

    assert result.exit_code == 0
    assert "CPF_CNPJ" in result.stdout
    assert "Contatos" in result.stdout


def test_inspect_document_shows_a_text_preview(tmp_path: Path) -> None:
    from waypoint_etl.demo.document_files import write_customers_txt

    source = write_customers_txt(tmp_path / "clientes.txt", count=3)

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == 0
    assert "CPF/CNPJ:" in result.stdout


def test_inspect_image_reports_missing_tesseract_as_controlled_error(
    tmp_path: Path,
) -> None:
    from waypoint_etl.demo.document_files import write_scanned_form_image
    from waypoint_etl.infrastructure.ocr.tesseract import TesseractEngine

    source = write_scanned_form_image(tmp_path / "ficha.png")
    available = TesseractEngine().is_available()

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == (0 if available else 2)
    assert "Traceback" not in result.stderr
    if available:
        assert "OCR:      sim" in result.stdout
    else:
        assert "Tesseract" in result.stderr


def test_inspect_rejects_unknown_format(tmp_path: Path) -> None:
    source = tmp_path / "dados.json"
    source.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == 2
    assert "não suportado" in result.stderr


def test_inspect_missing_file_is_a_controlled_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["inspect", str(tmp_path / "nao_existe.csv")])

    assert result.exit_code == 2
    assert "Traceback" not in result.stderr


# --- migrate ------------------------------------------------------------------


def test_migrate_dry_run_generates_the_four_files(
    workbook: Path, tmp_path: Path
) -> None:
    output = tmp_path / "exports"

    result = _migrate(workbook, output)

    run_dirs = list(output.iterdir())
    assert len(run_dirs) == 1

    run_dir = run_dirs[0]
    assert (run_dir / ACCEPTED_FILENAME).is_file()
    assert (run_dir / REJECTED_FILENAME).is_file()
    assert (run_dir / DUPLICATES_FILENAME).is_file()
    assert (run_dir / AUDIT_FILENAME).is_file()
    assert run_dir.name in result.stdout


def test_migrate_reports_the_totals(workbook: Path, tmp_path: Path) -> None:
    result = _migrate(workbook, tmp_path / "exports")

    assert "run_id:" in result.stdout
    assert "dry-run" in result.stdout
    assert "Total:" in result.stdout
    assert "Rejeitados:" in result.stdout


def test_migrate_exits_non_zero_when_there_are_rejected_records(
    workbook: Path, tmp_path: Path
) -> None:
    """Permite usar o comando em verificação automatizada."""
    result = _migrate(workbook, tmp_path / "exports")

    assert result.exit_code == 1


def test_migrate_exits_zero_when_everything_is_valid(tmp_path: Path) -> None:
    source = tmp_path / "limpo.csv"
    source.write_text(
        "Código,Nome Cliente,CPF_CNPJ,Correio Eletrônico,Fone Principal,CEP,"
        "Cidade,UF,Data Cadastro,Observação Interna Antiga\n"
        "ERP-1,Ana Silva,390.533.447-05,ana@exemplo.com.br,(11) 98765-4321,"
        "01310-100,São Paulo,SP,15/03/2024,\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(source),
            "--mapping",
            CUSTOMERS_CSV_TEMPLATE,
            "--output",
            str(tmp_path / "exports"),
        ],
    )

    assert result.exit_code == 0


def test_dry_run_never_writes_to_the_database(workbook: Path, tmp_path: Path) -> None:
    """Regra 15, na fronteira da CLI: as duas flags juntas são recusadas."""
    result = _migrate(workbook, tmp_path / "exports", "--load-postgres")

    assert result.exit_code == 2
    assert "--no-dry-run" in result.stderr


def test_load_without_database_url_is_a_controlled_error(
    workbook: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from waypoint_etl.config import get_settings

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    result = _migrate(workbook, tmp_path / "exports", "--no-dry-run", "--load-postgres")

    assert result.exit_code == 2
    assert "DATABASE_URL" in result.stderr
    assert "Traceback" not in result.stderr


def test_wrong_entity_is_rejected(workbook: Path, tmp_path: Path) -> None:
    result = _migrate(workbook, tmp_path / "exports", "--entity", "invoices")

    assert result.exit_code == 2
    assert "invoices" in result.stderr


def test_document_migrates_with_a_document_template(tmp_path: Path) -> None:
    """TXT percorre o mesmo pipeline de uma planilha e gera os artefatos."""
    from waypoint_etl.demo.document_files import write_customers_txt

    source = write_customers_txt(tmp_path / "clientes.txt", count=2)
    output = tmp_path / "exports"

    result = runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(source),
            "--mapping",
            "mappings/erp_legacy_customers_txt.yaml",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code in {0, 1}
    assert "Total:" in result.stdout
    assert list(output.iterdir())


def test_document_with_a_spreadsheet_template_points_at_the_format(
    tmp_path: Path,
) -> None:
    """Template declara um formato: aplicá-lo a outro falha com a causa real."""
    from waypoint_etl.demo.document_files import write_customers_txt

    source = write_customers_txt(tmp_path / "clientes.txt", count=2)

    result = _migrate(source, tmp_path / "exports")

    assert result.exit_code == 2
    assert "txt" in result.stderr.lower()


def test_invalid_template_fails_before_processing(
    workbook: Path, tmp_path: Path
) -> None:
    broken = tmp_path / "quebrado.yaml"
    broken.write_text("version: 1\nname: X\nentity: customers\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(workbook),
            "--mapping",
            str(broken),
            "--output",
            str(tmp_path / "exports"),
        ],
    )

    assert result.exit_code == 2
    assert "fields" in result.stderr


# --- conteúdo dos artefatos ---------------------------------------------------


def test_accepted_csv_uses_the_canonical_schema(workbook: Path, tmp_path: Path) -> None:
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    lines = (run_dir / ACCEPTED_FILENAME).read_text(encoding="utf-8").splitlines()

    assert lines[0].split(",")[:3] == ["external_id", "full_name", "document"]
    assert len(lines) > 1


def test_audit_report_has_the_required_metadata(workbook: Path, tmp_path: Path) -> None:
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    report = json.loads((run_dir / AUDIT_FILENAME).read_text(encoding="utf-8"))

    assert report["run"]["run_id"] == run_dir.name
    assert report["run"]["dry_run"] is True
    assert report["source"]["filename"] == workbook.name
    assert len(report["source"]["sha256"]) == 64
    assert report["mapping"]["name"]
    assert report["totals"]["total_records"] > 0
    assert report["waypoint_version"]


def test_audit_report_records_every_stage_duration(
    workbook: Path, tmp_path: Path
) -> None:
    """Seção 17: calcular a duração de cada estágio do pipeline."""
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    report = json.loads((run_dir / AUDIT_FILENAME).read_text(encoding="utf-8"))
    stages = [stage["name"] for stage in report["stages"]]

    assert stages == [
        "load_mapping",
        "extract",
        "map",
        "validate",
        "deduplicate",
        "export",
    ]
    assert all(stage["duration_ms"] >= 0 for stage in report["stages"])


def test_audit_report_masks_documents(workbook: Path, tmp_path: Path) -> None:
    """Seção 18: o relatório é artefato de leitura e não expõe CPF/CNPJ."""
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    report = json.loads((run_dir / AUDIT_FILENAME).read_text(encoding="utf-8"))
    document_issues = [
        issue
        for issue in report["issues"]["errors"]
        if issue["field"] == "document" and issue["original_value"]
    ]

    assert document_issues
    assert all("*" in issue["original_value"] for issue in document_issues)


def test_audit_report_has_no_secrets(workbook: Path, tmp_path: Path) -> None:
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    raw = (run_dir / AUDIT_FILENAME).read_text(encoding="utf-8").lower()

    assert "password" not in raw
    assert "postgresql://" not in raw
    assert "traceback" not in raw


def test_audit_report_counts_applied_transforms(workbook: Path, tmp_path: Path) -> None:
    """Seção 16: o relatório mostra as correções automáticas aplicadas."""
    output = tmp_path / "exports"
    _migrate(workbook, output)
    run_dir = next(output.iterdir())

    report = json.loads((run_dir / AUDIT_FILENAME).read_text(encoding="utf-8"))

    assert report["transforms_applied"]["digits_only"] > 0
    assert report["transforms_applied"]["title_case"] > 0


def test_csv_source_uses_its_own_template(tmp_path: Path) -> None:
    source = write_customers_csv(tmp_path / "clientes.csv", count=20)
    output = tmp_path / "exports"

    result = runner.invoke(
        app,
        [
            "migrate",
            "--input",
            str(source),
            "--mapping",
            CUSTOMERS_CSV_TEMPLATE,
            "--output",
            str(output),
        ],
    )

    assert result.exit_code in (0, 1)
    assert next(output.iterdir()).joinpath(ACCEPTED_FILENAME).is_file()


def test_template_declaring_another_format_is_rejected(tmp_path: Path) -> None:
    """O template de Excel aplicado a um CSV desalinharia o cabeçalho.

    Sem esta checagem o erro só apareceria como "coluna não encontrada", que não
    aponta a causa real.
    """
    source = write_customers_csv(tmp_path / "clientes.csv", count=5)

    result = _migrate(source, tmp_path / "exports")

    assert result.exit_code == 2
    assert "declara origem 'excel'" in result.stderr
