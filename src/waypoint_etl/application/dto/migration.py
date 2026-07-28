"""Contrato de uma execução de migração (seção 15).

Toda migração é rastreável por um ``run_id`` (regra 14), gerado no início e
propagado por logs, exportações e auditoria.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path

from ...domain.enums.entity_type import EntityType
from ...domain.enums.run_status import RunStatus

# Blocos de 1 MiB: evita carregar um arquivo grande inteiro em memória.
_HASH_CHUNK_SIZE = 1024 * 1024


def compute_file_hash(path: Path) -> str:
    """Calcula o SHA-256 do arquivo de origem.

    O hash identifica exatamente qual arquivo gerou a execução, permitindo
    reexecutar ou auditar sem guardar o conteúdo original (seção 15).
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class MigrationRun:
    """Metadados de uma execução, do início ao fim."""

    entity: EntityType
    source_filename: str
    source_hash: str
    dry_run: bool
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: RunStatus = RunStatus.RUNNING
    mapping_name: str | None = None
    mapping_version: int | None = None
    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    duplicate_records: int = 0
    ocr_used: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    duration_ms: int | None = None

    @property
    def run_id(self) -> str:
        """``run_id`` em texto, como aparece nos logs e no nome da pasta."""
        return str(self.id)

    def with_counters(
        self,
        *,
        total: int,
        valid: int,
        rejected: int,
        duplicates: int,
        ocr_used: bool = False,
    ) -> MigrationRun:
        """Devolve uma cópia com os totais preenchidos."""
        return replace(
            self,
            total_records=total,
            valid_records=valid,
            rejected_records=rejected,
            duplicate_records=duplicates,
            ocr_used=ocr_used,
        )

    def finish(
        self, status: RunStatus, *, finished_at: datetime | None = None
    ) -> MigrationRun:
        """Fecha a execução, calculando a duração."""
        end = finished_at if finished_at is not None else datetime.now(UTC)
        elapsed = int((end - self.started_at).total_seconds() * 1000)
        return replace(
            self, status=status, finished_at=end, duration_ms=max(elapsed, 0)
        )


__all__ = ["MigrationRun", "compute_file_hash"]
