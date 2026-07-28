"""Carga dos registros válidos no banco de destino (seção 15).

Duas garantias sustentam este módulo:

* ``dry-run`` **nunca** grava nas tabelas de destino (regra 15). A checagem é a
  primeira coisa que acontece, antes de qualquer conexão.
* a carga é atômica: erro de infraestrutura no meio do lote reverte tudo. Meia
  migração é pior do que nenhuma, porque não se sabe o que reprocessar.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...application.dto.migration import MigrationRun
from ...domain.enums.run_status import RunStatus
from ...domain.errors import WaypointError
from ...pipeline.validators.result import ValidatedRecord
from ..database.models import MigrationRunModel
from ..database.session import session_scope
from ..repositories.entities import add_entities, to_issue_model


class DryRunWriteAttemptError(WaypointError):
    """Tentativa de gravar durante um ``dry-run``.

    Indica erro de programação: a interface e a CLI devem impedir a carga antes
    de chegar aqui. Existe como última barreira da regra 15.
    """


class LoadError(WaypointError):
    """Falha de infraestrutura durante a carga. A transação foi revertida."""


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Resultado de uma carga concluída."""

    run: MigrationRun
    loaded_records: int
    loaded_issues: int


def load_records(
    engine: Engine, records: Sequence[ValidatedRecord], run: MigrationRun
) -> LoadResult:
    """Grava os registros válidos e a auditoria da execução, em uma transação.

    Registros rejeitados nunca vão para as tabelas de destino; suas issues, sim,
    para que o relatório fique rastreável pelo ``run_id``.
    """
    if run.dry_run:
        raise DryRunWriteAttemptError(
            "Execução em dry-run não pode gravar no banco. "
            "Use --no-dry-run para efetivar a carga."
        )

    valid = [record for record in records if record.is_valid]
    entities = [record.entity for record in valid if record.entity is not None]

    try:
        with session_scope(engine) as session:
            session.add(_to_run_model(run.finish(RunStatus.COMPLETED)))
            loaded = add_entities(session, entities, run.entity, run.id)
            issues = _add_issues(session, records, run)
    except SQLAlchemyError as error:
        # A transação já foi revertida pelo ``session_scope``; o relatório da
        # tentativa continua sendo gerado por quem chamou.
        raise LoadError(
            "Falha ao gravar no banco de dados: a carga foi revertida por "
            "completo e nenhum registro foi importado. Verifique a conexão e "
            "tente novamente."
        ) from error

    return LoadResult(
        run=run.finish(RunStatus.COMPLETED),
        loaded_records=loaded,
        loaded_issues=issues,
    )


def _add_issues(
    session: Session, records: Sequence[ValidatedRecord], run: MigrationRun
) -> int:
    """Grava as issues de todos os registros, já mascaradas."""
    models = [
        to_issue_model(issue, run.id, record.row_number)
        for record in records
        for issue in record.issues_for_display()
    ]
    session.add_all(models)
    return len(models)


def _to_run_model(run: MigrationRun) -> MigrationRunModel:
    """Converte o DTO da execução no modelo de auditoria."""
    return MigrationRunModel(
        id=run.id,
        status=run.status.value,
        entity=run.entity.value,
        source_filename=run.source_filename,
        source_hash=run.source_hash,
        mapping_name=run.mapping_name,
        mapping_version=run.mapping_version,
        dry_run=run.dry_run,
        total_records=run.total_records,
        valid_records=run.valid_records,
        rejected_records=run.rejected_records,
        duplicate_records=run.duplicate_records,
        ocr_used=run.ocr_used,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
    )


__all__ = [
    "DryRunWriteAttemptError",
    "LoadError",
    "LoadResult",
    "load_records",
]
