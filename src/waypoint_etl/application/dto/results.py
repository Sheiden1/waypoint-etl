"""Resultados dos casos de uso, compartilhados por CLI e Streamlit.

As duas interfaces consomem exatamente estes objetos (seção 5): nenhuma regra
de negócio pode viver na camada de apresentação.
"""

from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat
from ...pipeline.deduplication.detector import DeduplicationResult
from ...pipeline.validators.result import ValidatedRecord
from .migration import MigrationRun


@dataclass(frozen=True, slots=True)
class StageDuration:
    """Duração de um estágio do pipeline (seção 17)."""

    name: str
    duration_ms: int


class StageTimer:
    """Acumula a duração de cada estágio de uma execução."""

    def __init__(self) -> None:
        self._stages: list[StageDuration] = []

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        """Mede o tempo do bloco e registra sob ``name``."""
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - started) * 1000
            self._stages.append(StageDuration(name=name, duration_ms=int(elapsed)))

    @property
    def stages(self) -> tuple[StageDuration, ...]:
        """Estágios medidos, na ordem de execução."""
        return tuple(self._stages)


@dataclass(frozen=True, slots=True)
class SourcePreview:
    """Prévia do conteúdo de um arquivo, usada pelo comando ``inspect``."""

    source_name: str
    source_format: SourceFormat
    is_tabular: bool
    columns: tuple[str, ...] = ()
    rows: tuple[Mapping[str, str | None], ...] = ()
    available_sheets: tuple[str, ...] = ()
    text_preview: str | None = None
    page_count: int | None = None
    ocr_used: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Resultado completo de uma migração, em ``dry-run`` ou efetivada."""

    run: MigrationRun
    entity: EntityType
    records: tuple[ValidatedRecord, ...]
    duplicates: DeduplicationResult
    stages: tuple[StageDuration, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    output_dir: Path | None = None
    exported_files: tuple[Path, ...] = field(default_factory=tuple)
    loaded_records: int = 0
    transforms_applied: Mapping[str, int] = field(default_factory=dict)
    """Quantas vezes cada transformação do De/Para alterou algum valor."""

    @property
    def accepted(self) -> tuple[ValidatedRecord, ...]:
        """Registros aptos a serem importados."""
        return tuple(record for record in self.records if record.is_valid)

    @property
    def rejected(self) -> tuple[ValidatedRecord, ...]:
        """Registros bloqueados por ao menos um erro."""
        return tuple(record for record in self.records if not record.is_valid)

    @property
    def total_records(self) -> int:
        """Total de registros lidos da origem."""
        return len(self.records)

    @property
    def duplicate_count(self) -> int:
        """Quantidade de duplicatas exatas encontradas."""
        return len(self.duplicates.exact)

    @property
    def possible_duplicate_count(self) -> int:
        """Quantidade de suspeitas de duplicidade."""
        return len(self.duplicates.possible)

    @property
    def run_id(self) -> str:
        """Identificador da execução."""
        return self.run.run_id


__all__ = [
    "MigrationResult",
    "SourcePreview",
    "StageDuration",
    "StageTimer",
]
