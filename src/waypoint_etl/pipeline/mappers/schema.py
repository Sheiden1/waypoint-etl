"""Modelo do template De/Para carregado do YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from ...application.dto.extraction import ExtractionOptions
from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat
from ...domain.services.canonical_schema import required_field_names

SUPPORTED_TEMPLATE_VERSION = 1


@dataclass(frozen=True, slots=True)
class FieldMapping:
    """Ligação entre uma coluna de origem e um campo canônico."""

    source: str
    target: str
    required: bool = False
    transforms: tuple[str, ...] = field(default_factory=tuple)
    default: str | None = None


class RecordMode(StrEnum):
    """Como um documento textual é dividido em registros."""

    PAGE = "page"
    SEPARATOR = "separator"


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Bloco ``source`` do template: como ler o arquivo.

    ``record_mode``, ``record_separator`` e ``label_separator`` só se aplicam a
    documentos (TXT, DOCX, PDF, imagem), que não têm linhas e colunas.
    """

    type: SourceFormat | None = None
    sheet: str | None = None
    header_row: int = 1
    encoding: str | None = None
    delimiter: str | None = None
    record_mode: RecordMode = RecordMode.PAGE
    record_separator: str | None = None
    label_separator: str = ":"

    def to_extraction_options(self) -> ExtractionOptions:
        """Converte a declaração do template nas opções do extrator."""
        return ExtractionOptions(
            sheet=self.sheet,
            header_row=self.header_row,
            encoding=self.encoding,
            delimiter=self.delimiter,
        )


@dataclass(frozen=True, slots=True)
class MappingTemplate:
    """Template De/Para completo e já validado."""

    name: str
    entity: EntityType
    fields: tuple[FieldMapping, ...]
    version: int = SUPPORTED_TEMPLATE_VERSION
    source: SourceSpec = field(default_factory=SourceSpec)
    ignored_fields: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source_columns(self) -> tuple[str, ...]:
        """Colunas de origem esperadas pelo template."""
        return tuple(mapping.source for mapping in self.fields)

    @property
    def target_fields(self) -> tuple[str, ...]:
        """Campos canônicos preenchidos pelo template."""
        return tuple(mapping.target for mapping in self.fields)

    def mapping_for_target(self, target: str) -> FieldMapping | None:
        """Devolve o mapeamento que preenche ``target``, se houver."""
        for mapping in self.fields:
            if mapping.target == target:
                return mapping
        return None

    def _is_blocking(self, mapping: FieldMapping) -> bool:
        """Indica se a ausência da coluna impede a migração.

        Bloqueia quando o destino é obrigatório no schema canônico — sem ele o
        registro perde identidade — ou quando o próprio template exige o campo.
        """
        return mapping.required or mapping.target in required_field_names(self.entity)

    def missing_blocking_columns(self, available: tuple[str, ...]) -> tuple[str, ...]:
        """Colunas ausentes cuja falta impede processar o arquivo."""
        present = set(available)
        return tuple(
            mapping.source
            for mapping in self.fields
            if mapping.source not in present and self._is_blocking(mapping)
        )

    def missing_tolerable_columns(self, available: tuple[str, ...]) -> tuple[str, ...]:
        """Colunas ausentes que apenas deixam o campo canônico sem origem."""
        present = set(available)
        return tuple(
            mapping.source
            for mapping in self.fields
            if mapping.source not in present and not self._is_blocking(mapping)
        )


__all__ = [
    "SUPPORTED_TEMPLATE_VERSION",
    "FieldMapping",
    "MappingTemplate",
    "RecordMode",
    "SourceSpec",
]
