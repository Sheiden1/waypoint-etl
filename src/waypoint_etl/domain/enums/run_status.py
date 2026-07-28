"""Status de uma execução de migração."""

from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    """Situação de uma execução registrada em ``migration_runs``."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN = "dry_run"
