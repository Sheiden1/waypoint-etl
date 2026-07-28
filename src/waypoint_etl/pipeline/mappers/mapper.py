"""Aplicação do template De/Para sobre os registros extraídos.

Converte ``SourceRecord`` (colunas da origem) em ``MappedRecord`` (campos
canônicos, ainda como texto). Registra o que foi transformado, para o relatório
de auditoria conseguir mostrar as correções automáticas (seção 16).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ...application.dto.extraction import ExtractionResult, SourceRecord
from .loader import MappingError
from .schema import MappingTemplate
from .transforms import apply_transforms


@dataclass(frozen=True, slots=True)
class MappedRecord:
    """Registro já no vocabulário canônico, antes da validação de tipos."""

    row_number: int
    values: Mapping[str, str | None]
    sheet: str | None = None
    applied_transforms: tuple[str, ...] = field(default_factory=tuple)

    def get(self, target: str) -> str | None:
        """Valor de um campo canônico (``None`` quando ausente)."""
        return self.values.get(target)


@dataclass(frozen=True, slots=True)
class MappingResult:
    """Resultado da aplicação do template a um lote de registros."""

    records: tuple[MappedRecord, ...]
    template_name: str
    unmapped_columns: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def record_count(self) -> int:
        """Quantidade de registros mapeados."""
        return len(self.records)


def apply_mapping(
    extraction: ExtractionResult, template: MappingTemplate
) -> MappingResult:
    """Aplica o template a um resultado de extração.

    Falha antes de processar qualquer linha quando o arquivo não tem as colunas
    declaradas — problema de configuração não deve virar lote inteiro rejeitado.
    """
    missing = template.missing_columns(extraction.columns)
    if missing:
        listed = ", ".join(missing)
        available = ", ".join(extraction.columns)
        raise MappingError(
            f"O template '{template.name}' espera a(s) coluna(s) {listed}, que "
            f"não existe(m) em '{extraction.source_name}'. "
            f"Colunas encontradas: {available}."
        )

    records = tuple(map_record(record, template) for record in extraction.records)
    return MappingResult(
        records=records,
        template_name=template.name,
        unmapped_columns=_unmapped_columns(extraction.columns, template),
        warnings=_build_warnings(extraction.columns, template),
    )


def map_record(record: SourceRecord, template: MappingTemplate) -> MappedRecord:
    """Converte um único registro de origem para o vocabulário canônico."""
    values: dict[str, str | None] = {}
    applied: list[str] = []

    for mapping in template.fields:
        raw = record.values.get(mapping.source)
        transformed = apply_transforms(raw, mapping.transforms)
        if transformed is None and mapping.default is not None:
            transformed = mapping.default
        if transformed != raw:
            applied.extend(mapping.transforms)
        values[mapping.target] = transformed

    return MappedRecord(
        row_number=record.row_number,
        values=values,
        sheet=record.sheet,
        applied_transforms=tuple(dict.fromkeys(applied)),
    )


def _unmapped_columns(
    columns: tuple[str, ...], template: MappingTemplate
) -> tuple[str, ...]:
    """Colunas presentes no arquivo que o template não usa nem ignora."""
    mapped = set(template.source_columns)
    ignored = set(template.ignored_fields)
    return tuple(
        column for column in columns if column not in mapped and column not in ignored
    )


def _build_warnings(
    columns: tuple[str, ...], template: MappingTemplate
) -> tuple[str, ...]:
    """Avisa sobre colunas que serão descartadas sem declaração explícita."""
    unmapped = _unmapped_columns(columns, template)
    if not unmapped:
        return ()
    listed = ", ".join(unmapped)
    return (
        f"Coluna(s) não mapeada(s) e descartada(s): {listed}. "
        "Declare em 'ignored_fields' para tornar o descarte explícito.",
    )


__all__ = [
    "MappedRecord",
    "MappingResult",
    "apply_mapping",
    "map_record",
]
