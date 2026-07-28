"""Resultado da validação de um registro."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ...domain.entities.contact import Contact
from ...domain.entities.customer import Customer
from ...domain.entities.invoice import Invoice
from ...domain.enums.entity_type import EntityType
from ...domain.value_objects.issue import Issue

CanonicalEntity = Customer | Contact | Invoice


@dataclass(frozen=True, slots=True)
class ValidatedRecord:
    """Um registro após a validação, aceito ou rejeitado.

    ``entity`` só é preenchido quando o registro é válido. Os ``values``
    originais são preservados sempre, porque o relatório de rejeitados precisa
    mostrar o que veio da origem.
    """

    row_number: int
    entity_type: EntityType
    values: Mapping[str, str | None]
    issues: tuple[Issue, ...] = field(default_factory=tuple)
    entity: CanonicalEntity | None = None
    sheet: str | None = None

    @property
    def errors(self) -> tuple[Issue, ...]:
        """Problemas que rejeitam o registro."""
        return tuple(issue for issue in self.issues if issue.is_error)

    @property
    def warnings(self) -> tuple[Issue, ...]:
        """Alertas que não impedem a importação."""
        return tuple(issue for issue in self.issues if issue.is_warning)

    @property
    def is_valid(self) -> bool:
        """Indica que o registro pode ser importado."""
        return not self.errors

    def issues_for_display(self) -> tuple[Issue, ...]:
        """Issues com documentos mascarados, prontas para exibição."""
        return tuple(issue.for_display() for issue in self.issues)


__all__ = ["CanonicalEntity", "ValidatedRecord"]
