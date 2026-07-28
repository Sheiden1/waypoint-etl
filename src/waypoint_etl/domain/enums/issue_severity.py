"""Severidade de problemas de validação."""

from __future__ import annotations

from enum import StrEnum


class IssueSeverity(StrEnum):
    """Severidade de um problema encontrado durante a validação.

    Um ``ERROR`` rejeita o registro; um ``WARNING`` permite a importação, mas
    aparece no relatório de auditoria.
    """

    WARNING = "warning"
    ERROR = "error"
