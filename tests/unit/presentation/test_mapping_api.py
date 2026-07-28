"""Contratos HTTP do catálogo e upload de templates."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from waypoint_etl.presentation.api.mapping_routes import create_mapping_router


def _client(mappings_dir: Path = Path("mappings")) -> TestClient:
    app = FastAPI()
    app.include_router(create_mapping_router(mappings_dir))
    return TestClient(app)


def test_catalog_lists_and_filters_versioned_templates() -> None:
    response = _client().get(
        "/api/v1/mappings",
        params={"entity": "customers", "source_format": "csv"},
    )

    assert response.status_code == 200
    templates = response.json()["templates"]
    assert [template["template_id"] for template in templates] == [
        "erp_legacy_customers_csv"
    ]
    template = templates[0]
    assert template["entity"] == "customers"
    assert template["source_format"] == "csv"
    assert template["assignments"]["Nome Cliente"] == "full_name"
    assert "version: 1" in template["content"]


def test_catalog_reports_an_invalid_versioned_template(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("fields: [", encoding="utf-8")

    response = _client(tmp_path).get("/api/v1/mappings")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "mapping_catalog_invalid"


def test_preview_validates_an_uploaded_mapping() -> None:
    mapping = Path("mappings/erp_legacy_customers_csv.yaml")

    response = _client().post(
        "/api/v1/mappings/preview",
        files={
            "mapping": (
                "meu-template.yaml",
                mapping.read_bytes(),
                "application/yaml",
            )
        },
        data={"entity": "customers", "source_format": "csv"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["template_id"] == "uploaded"
    assert payload["filename"] == "meu-template.yaml"
    assert payload["assignments"]["CPF_CNPJ"] == "document"


def test_preview_rejects_incompatible_format() -> None:
    mapping = Path("mappings/erp_legacy_customers_csv.yaml")

    response = _client().post(
        "/api/v1/mappings/preview",
        files={"mapping": ("mapping.yaml", mapping.read_bytes())},
        data={"entity": "customers", "source_format": "excel"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "mapping_format_mismatch"


def test_preview_rejects_invalid_yaml() -> None:
    response = _client().post(
        "/api/v1/mappings/preview",
        files={"mapping": ("mapping.yaml", b"fields: [")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "mapping_invalid"
