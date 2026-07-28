"""Contratos dos artefatos de distribuição e colaboração."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def test_required_open_source_files_exist() -> None:
    required = (
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "Dockerfile",
        "LICENSE",
        "README.md",
        "SECURITY.md",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        ".github/pull_request_template.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
    )

    missing = [name for name in required if not (ROOT / name).is_file()]

    assert missing == []


def test_compose_defines_app_database_healthcheck_and_persistent_volumes() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    assert set(compose["services"]) == {"app", "db"}
    assert compose["services"]["db"]["healthcheck"]
    assert (
        compose["services"]["app"]["depends_on"]["db"]["condition"] == "service_healthy"
    )
    assert set(compose["volumes"]) == {"exports", "postgres-data"}


def test_ci_runs_quality_ocr_postgres_and_package_build() -> None:
    raw = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "tesseract-ocr-por" in raw
    assert "WAYPOINT_TEST_DATABASE_URL" in raw
    assert "uv run ruff check ." in raw
    assert "uv run mypy" in raw
    assert "uv run pytest --cov=waypoint_etl" in raw
    assert "uv build" in raw
    assert "docker compose up --build --detach" in raw
    assert "http://127.0.0.1:8501/_stcore/health" in raw


def test_expected_customer_snapshot_matches_versioned_sample() -> None:
    snapshot = json.loads(
        (ROOT / "samples/expected/customers-summary.json").read_text(encoding="utf-8")
    )

    assert snapshot["source"]["filename"] == "clientes_legado.csv"
    assert snapshot["totals"] == {
        "total_records": 55,
        "valid_records": 45,
        "rejected_records": 10,
        "duplicate_records": 4,
        "possible_duplicates": 0,
    }
