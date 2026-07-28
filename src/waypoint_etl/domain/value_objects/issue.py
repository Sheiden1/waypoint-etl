"""Problema encontrado durante a validação de um registro (seção 13).

Um ``error`` rejeita o registro; um ``warning`` permite a importação, mas
aparece no relatório. A mensagem é escrita para o usuário e deve sugerir uma
ação (seção 17), nunca expor stack trace.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..enums.document_type import DocumentType
from ..enums.issue_severity import IssueSeverity
from .document import mask_document

# Campos cujo valor nunca deve aparecer inteiro em auditoria (seção 18).
SENSITIVE_FIELDS: frozenset[str] = frozenset({"document", "customer_document"})


@dataclass(frozen=True, slots=True)
class Issue:
    """Um problema de qualidade associado a um campo de um registro."""

    code: str
    message: str
    severity: IssueSeverity
    field: str | None = None
    original_value: str | None = None
    normalized_value: str | None = None

    @property
    def is_error(self) -> bool:
        """Indica se este problema rejeita o registro."""
        return self.severity is IssueSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        """Indica se este problema apenas alerta."""
        return self.severity is IssueSeverity.WARNING

    def for_display(self) -> Issue:
        """Versão segura para exibição, com documentos mascarados.

        Use ao enviar issues para a interface ou para o relatório de auditoria:
        CPF/CNPJ completos não podem aparecer (seção 18).
        """
        if self.field not in SENSITIVE_FIELDS:
            return self
        return Issue(
            code=self.code,
            message=self.message,
            severity=self.severity,
            field=self.field,
            original_value=_mask(self.original_value),
            normalized_value=_mask(self.normalized_value),
        )


def _mask(value: str | None) -> str | None:
    """Mascara um valor sensível, preservando ``None``."""
    return None if value is None else mask_document(value)


def error(
    code: str,
    message: str,
    *,
    field: str | None = None,
    original_value: str | None = None,
    normalized_value: str | None = None,
) -> Issue:
    """Cria um problema que rejeita o registro."""
    return Issue(
        code=code,
        message=message,
        severity=IssueSeverity.ERROR,
        field=field,
        original_value=original_value,
        normalized_value=normalized_value,
    )


def warning(
    code: str,
    message: str,
    *,
    field: str | None = None,
    original_value: str | None = None,
    normalized_value: str | None = None,
) -> Issue:
    """Cria um alerta que não impede a importação."""
    return Issue(
        code=code,
        message=message,
        severity=IssueSeverity.WARNING,
        field=field,
        original_value=original_value,
        normalized_value=normalized_value,
    )


def describe_document_type(document_type: DocumentType) -> str:
    """Nome do tipo de documento para uso em mensagens ao usuário."""
    return "CPF" if document_type is DocumentType.CPF else "CNPJ"


__all__ = [
    "SENSITIVE_FIELDS",
    "Issue",
    "describe_document_type",
    "error",
    "warning",
]
