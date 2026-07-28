"""Contratos da primeira fatia da API web."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from waypoint_etl.config import Settings
from waypoint_etl.demo.synthetic import write_customers_csv
from waypoint_etl.infrastructure.database.models import CustomerModel
from waypoint_etl.infrastructure.database.session import (
    create_all,
    create_database_engine,
    session_scope,
)
from waypoint_etl.infrastructure.reports.artifact_store import TemporaryArtifactStore
from waypoint_etl.presentation.api.app import create_app


def _client(
    *,
    max_upload_mb: int = 25,
    database_url: str | None = None,
    artifact_store: TemporaryArtifactStore | None = None,
) -> TestClient:
    settings = Settings(
        max_upload_mb=max_upload_mb,
        web_origins="http://localhost",
        database_url=database_url,
    )
    return TestClient(create_app(settings, artifact_store=artifact_store))


def _migration_files() -> dict[str, tuple[str, bytes, str]]:
    source = Path("samples/input/clientes_legado.csv")
    mapping = Path("mappings/erp_legacy_customers_csv.yaml")
    return {
        "file": ("clientes_legado.csv", source.read_bytes(), "text/csv"),
        "mapping": (
            "clientes-mapping.yaml",
            mapping.read_bytes(),
            "application/yaml",
        ),
    }


def test_health_describes_optional_features() -> None:
    response = _client().get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["max_upload_mb"] == 25
    assert set(response.json()["features"]) == {"ocr", "database"}


def test_application_exposes_the_mapping_catalog() -> None:
    response = _client().get(
        "/api/v1/mappings",
        params={"entity": "customers", "source_format": "csv"},
    )

    assert response.status_code == 200
    assert [template["template_id"] for template in response.json()["templates"]] == [
        "erp_legacy_customers_csv"
    ]


def test_inspect_upload_uses_the_real_inspection_case(
    tmp_path: Path,
) -> None:
    source = write_customers_csv(tmp_path / "clientes.csv", count=3)

    response = _client().post(
        "/api/v1/inspect",
        files={"file": ("../../clientes.csv", source.read_bytes(), "text/csv")},
        data={"header_row": "1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_name"] == "clientes.csv"
    assert payload["source_format"] == "csv"
    assert payload["is_tabular"] is True
    assert "CPF_CNPJ" in payload["columns"]
    assert len(payload["rows"]) >= 3


def test_inspect_rejects_empty_upload() -> None:
    response = _client().post(
        "/api/v1/inspect",
        files={"file": ("clientes.csv", b"", "text/csv")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "empty_upload"


def test_inspect_rejects_unsupported_format() -> None:
    response = _client().post(
        "/api/v1/inspect",
        files={
            "file": (
                "clientes.exe",
                b"not-an-executable",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "inspection_failed"
    assert "Formato não suportado" in response.json()["detail"]["message"]


def test_inspect_stops_when_upload_exceeds_limit() -> None:
    response = _client(max_upload_mb=1).post(
        "/api/v1/inspect",
        files={
            "file": (
                "clientes.csv",
                b"x" * (1024 * 1024 + 1),
                "text/csv",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "upload_too_large"


def test_dry_run_executes_the_real_pipeline_and_returns_quality_result() -> None:
    client = _client()
    response = client.post(
        "/api/v1/migrations/dry-run",
        files=_migration_files(),
        data={"entity": "customers"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["status"] == "dry_run"
    assert payload["entity"] == "customers"
    assert payload["summary"] == {
        "total": 55,
        "valid": 45,
        "rejected": 10,
        "duplicates": 4,
        "possible_duplicates": 0,
        "duration_ms": payload["summary"]["duration_ms"],
    }
    assert payload["run_id"]
    assert payload["issues"]
    assert payload["stages"][-1]["name"] == "export"
    assert payload["transforms_applied"]
    assert payload["artifacts_expires_in_seconds"] == 1800
    assert {artifact["name"] for artifact in payload["artifacts"]} == {
        "accepted.csv",
        "rejected.xlsx",
        "duplicates.csv",
        "audit-report.json",
    }
    assert all(
        "*" in row["document"]
        for row in payload["accepted_rows"]
        if row.get("document")
    )

    for artifact in payload["artifacts"]:
        download = client.get(artifact["download_url"])
        assert download.status_code == 200
        assert download.content
        assert download.headers["cache-control"] == "private, no-store"
        assert artifact["name"] in download.headers["content-disposition"]


def test_dry_run_keeps_only_generated_artifacts(tmp_path: Path) -> None:
    store = TemporaryArtifactStore(ttl_seconds=300, root=tmp_path / "artifacts")
    client = _client(artifact_store=store)

    response = client.post(
        "/api/v1/migrations/dry-run",
        files=_migration_files(),
        data={"entity": "customers"},
    )

    assert response.status_code == 200
    run_dir = store.root / response.json()["run_id"]
    assert {path.name for path in run_dir.iterdir()} == {
        "accepted.csv",
        "rejected.xlsx",
        "duplicates.csv",
        "audit-report.json",
    }
    assert not (run_dir / "clientes_legado.csv").exists()
    assert not (run_dir / "clientes-mapping.yaml").exists()


def test_download_rejects_unknown_artifact_name() -> None:
    client = _client()
    dry_run = client.post(
        "/api/v1/migrations/dry-run",
        files=_migration_files(),
        data={"entity": "customers"},
    ).json()

    response = client.get(
        f"/api/v1/migrations/{dry_run['run_id']}/artifacts/segredo.env"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "artifact_not_found"


def test_download_rejects_unknown_run() -> None:
    response = _client().get(
        f"/api/v1/migrations/{uuid.uuid4()}/artifacts/accepted.csv"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


def test_dry_run_rejects_an_invalid_mapping() -> None:
    response = _client().post(
        "/api/v1/migrations/dry-run",
        files={
            "file": ("clientes.csv", b"nome,documento\nAda,123", "text/csv"),
            "mapping": ("mapping.yaml", b"fields: [", "application/yaml"),
        },
        data={"entity": "customers"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "dry_run_failed"
    assert "YAML válido" in response.json()["detail"]["message"]


def test_dry_run_rejects_an_empty_mapping() -> None:
    response = _client().post(
        "/api/v1/migrations/dry-run",
        files={
            "file": ("clientes.csv", b"nome,documento\nAda,123", "text/csv"),
            "mapping": ("mapping.yaml", b"", "application/yaml"),
        },
        data={"entity": "customers"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "empty_mapping"


def test_database_load_requires_explicit_confirmation(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'waypoint.db'}"

    response = _client(database_url=database_url).post(
        "/api/v1/migrations/load-postgres",
        files=_migration_files(),
        data={"entity": "customers", "confirm": "false"},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "confirmation_required"


def test_database_load_is_clear_when_database_is_not_configured() -> None:
    response = _client(database_url=None).post(
        "/api/v1/migrations/load-postgres",
        files=_migration_files(),
        data={"entity": "customers", "confirm": "true"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "database_unavailable"
    assert "DATABASE_URL" in response.json()["detail"]["message"]


def test_confirmed_database_load_persists_valid_records(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'waypoint.db'}"
    engine = create_database_engine(database_url)
    create_all(engine)
    engine.dispose()
    client = _client(database_url=database_url)

    response = client.post(
        "/api/v1/migrations/load-postgres",
        files=_migration_files(),
        data={"entity": "customers", "confirm": "true"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is False
    assert payload["status"] == "completed"
    assert payload["loaded_records"] == 45
    assert payload["summary"]["valid"] == 45
    assert len(payload["artifacts"]) == 4

    verification_engine = create_database_engine(database_url)
    with session_scope(verification_engine) as session:
        stored = session.scalar(select(func.count()).select_from(CustomerModel))
    verification_engine.dispose()
    assert stored == 45
