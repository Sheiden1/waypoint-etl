"""Port de extração implementado pela camada de infraestrutura."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ...domain.enums.source_format import SourceFormat
from ..dto.document import DocumentText
from ..dto.extraction import ExtractionOptions, ExtractionResult


@runtime_checkable
class TabularExtractor(Protocol):
    """Lê um arquivo tabular de origem e devolve registros brutos.

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


@runtime_checkable
class DocumentExtractor(Protocol):
    """Lê um documento textual e devolve seu texto por página.

    A estruturação em registros acontece depois, no estágio de Regex; aqui o
    compromisso é apenas entregar o texto o mais fiel possível ao original.
    """

    @property
    def source_format(self) -> SourceFormat:
        """Formato atendido por este extrator."""
        ...

    def supports(self, path: Path) -> bool:
        """Indica se este extrator consegue ler ``path``."""
        ...

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        """Lê ``path`` e devolve o texto do documento."""
        ...


__all__ = ["DocumentExtractor", "TabularExtractor"]
