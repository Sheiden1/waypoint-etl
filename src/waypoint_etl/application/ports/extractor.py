"""Port de extração implementado pela camada de infraestrutura."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ...domain.enums.source_format import SourceFormat
from ..dto.extraction import ExtractionOptions, ExtractionResult


@runtime_checkable
class Extractor(Protocol):
    """Lê um arquivo de origem e devolve registros brutos.

    Implementações não devem interromper o lote por causa de uma linha
    problemática: apenas o arquivo inválido como um todo gera
    ``ExtractionError``.
    """

    @property
    def source_format(self) -> SourceFormat:
        """Formato atendido por este extrator."""
        ...

    def supports(self, path: Path) -> bool:
        """Indica se este extrator consegue ler ``path``."""
        ...

    def extract(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> ExtractionResult:
        """Lê ``path`` e devolve os registros de origem."""
        ...


__all__ = ["Extractor"]
