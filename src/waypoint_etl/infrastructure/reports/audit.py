"""Relatório de auditoria em JSON (seção 16).

O relatório é o artefato de **leitura** da execução: por isso os documentos
aparecem mascarados e nenhuma string de conexão, segredo ou stack trace entra
aqui (seção 16, último parágrafo).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from ... import __version__
from ...application.dto.results import MigrationResult
from ...domain.value_objects.issue import Issue

AUDIT_FILENAME = "audit-report.json"

# Limite de issues detalhadas no relatório. Acima disso o arquivo deixaria de
# ser legível; os totais por código continuam completos.
MAX_DETAILED_ISSUES = 500


def build_audit_report(result: MigrationResult) -> dict[str, Any]:
    """Monta o conteúdo do relatório de auditoria."""
    run = result.run
    return {
        "waypoint_version": __version__,
        "run": {
            "run_id": run.run_id,
            "status": run.status.value,
            "entity": run.entity.value,
            "dry_run": run.dry_run,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
        },
        "source": {
            "filename": run.source_filename,
            "sha256": run.source_hash,
            "ocr_used": run.ocr_used,
        },
        "mapping": {
            "name": run.mapping_name,
            "version": run.mapping_version,
        },
        "totals": {
            "total_records": result.total_records,
            "valid_records": len(result.accepted),
            "rejected_records": len(result.rejected),
            "duplicate_records": result.duplicate_count,
            "possible_duplicates": result.possible_duplicate_count,
            "loaded_records": result.loaded_records,
        },
        "stages": [
            {"name": stage.name, "duration_ms": stage.duration_ms}
            for stage in result.stages
        ],
        "transforms_applied": dict(sorted(result.transforms_applied.items())),
        "issues": {
            "by_code": _issue_counts(result),
            "errors": _issue_details(result, severity="error"),
            "warnings": _issue_details(result, severity="warning"),
        },
        "duplicates": {
            "exact": [
                {
                    "row": match.row_number,
                    "matched_row": match.matched_row_number,
                    "key": match.key,
                }
                for match in result.duplicates.exact
            ],
            "possible": [
                {
                    "row": match.row_number,
                    "matched_row": match.matched_row_number,
                    "key": match.key,
                    "similarity": match.similarity,
                }
                for match in result.duplicates.possible
            ],
        },
        "warnings": list(result.warnings),
    }


def write_audit_report(path: Path, result: MigrationResult) -> Path:
    """Escreve o relatório de auditoria em ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_audit_report(result)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _issue_counts(result: MigrationResult) -> dict[str, int]:
    """Total de ocorrências por código de problema."""
    counter: Counter[str] = Counter()
    for record in result.records:
        counter.update(issue.code for issue in record.issues)
    return dict(sorted(counter.items()))


def _issue_details(result: MigrationResult, *, severity: str) -> list[dict[str, Any]]:
    """Detalha as issues de uma severidade, com documentos já mascarados."""
    details: list[dict[str, Any]] = []
    for record in result.records:
        for issue in record.issues_for_display():
            if issue.severity.value != severity:
                continue
            if len(details) >= MAX_DETAILED_ISSUES:
                return details
            details.append(_issue_payload(issue, record.row_number))
    return details


def _issue_payload(issue: Issue, row_number: int) -> dict[str, Any]:
    """Converte uma issue no formato do relatório."""
    return {
        "row": row_number,
        "code": issue.code,
        "field": issue.field,
        "message": issue.message,
        "original_value": issue.original_value,
        "normalized_value": issue.normalized_value,
    }


__all__ = [
    "AUDIT_FILENAME",
    "MAX_DETAILED_ISSUES",
    "build_audit_report",
    "write_audit_report",
]
