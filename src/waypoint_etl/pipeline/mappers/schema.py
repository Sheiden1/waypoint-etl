"""Modelo do template De/Para carregado do YAML."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...application.dto.extraction import ExtractionOptions
from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat

SUPPORTED_TEMPLATE_VERSION = 1


@dataclass(frozen=True, slots=True)
class FieldMapping:
    """Ligação entre uma coluna de origem e um campo canônico."""

    source: str
    target: str
    required: bool = False
    transforms: tuple[str, ...] = field(default_factory=tuple)
    default: str | None = None


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Bloco ``source`` do template: como ler o arquivo."""

    type: SourceFormat | None = None
    sheet: str | None = None
    header_row: int = 1
    encoding: str | None = None
    delimiter: str | None = None

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

    def missing_columns(self, available: tuple[str, ...]) -> tuple[str, ...]:
        """Colunas declaradas no template que não existem no arquivo lido."""
        present = set(available)
        return tuple(
            mapping.source for mapping in self.fields if mapping.source not in present
        )


__all__ = [
    "SUPPORTED_TEMPLATE_VERSION",
    "FieldMapping",
    "MappingTemplate",
    "SourceSpec",
]
