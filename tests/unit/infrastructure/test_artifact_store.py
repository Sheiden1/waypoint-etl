"""Armazenamento temporário dos relatórios disponibilizados pela API."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from waypoint_etl.infrastructure.reports.artifact_store import (
    ARTIFACT_SPECS,
    ArtifactRunNotFoundError,
    TemporaryArtifactStore,
)


def test_artifacts_expire_without_retaining_other_files(tmp_path: Path) -> None:
    now = [1_000.0]
    generated = tmp_path / "generated"
    generated.mkdir()
    files = []
    for spec in ARTIFACT_SPECS:
        path = generated / spec.name
        path.write_bytes(f"conteúdo de {spec.name}".encode())
        files.append(path)
    upload = generated / "clientes.csv"
    upload.write_text("dado original", encoding="utf-8")

    store = TemporaryArtifactStore(
        ttl_seconds=60,
        root=tmp_path / "published",
        clock=lambda: now[0],
    )
    run_id = str(uuid.uuid4())
    store.publish(run_id, files)

    published = store.root / run_id
    assert {path.name for path in published.iterdir()} == {
        spec.name for spec in ARTIFACT_SPECS
    }
    assert store.resolve(run_id, "accepted.csv").path.read_text() != "dado original"

    now[0] += 61
    with pytest.raises(ArtifactRunNotFoundError, match="expirada"):
        store.resolve(run_id, "accepted.csv")

    assert not published.exists()
