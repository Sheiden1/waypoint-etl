"""Contratos da etapa de extração.

Cada estágio do pipeline recebe e devolve objetos explícitos (seção 6). A
extração devolve sempre valores textuais brutos: limpeza, normalização e
conversão de tipos acontecem nos estágios seguintes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ...domain.enums.source_format import SourceFormat


@dataclass(frozen=True, slots=True)
class ExtractionOptions:
    """Opções de leitura declaradas pelo template De/Para (bloco ``source``)."""

    sheet: str | None = None
    """Nome da aba a ler. ``None`` usa a primeira aba da planilha."""

    header_row: int = 1
    """Linha (1-based) que contém o cabeçalho. Linhas anteriores são ignoradas."""

    encoding: str | None = None
    """Codificação do arquivo de texto. ``None`` tenta uma lista de candidatas."""

    delimiter: str | None = None
    """Delimitador do CSV. ``None`` detecta automaticamente."""


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Uma linha bruta do arquivo de origem.

    ``row_number`` é a linha real dentro do arquivo (1-based, contando o
    cabeçalho) para que qualquer rejeição seja rastreável até a origem.
    """

    row_number: int
    values: Mapping[str, str | None]
    sheet: str | None = None


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Resultado da leitura de um arquivo de origem."""

    source_name: str
    source_format: SourceFormat
    columns: tuple[str, ...]
    records: tuple[SourceRecord, ...]
    sheet: str | None = None
    available_sheets: tuple[str, ...] = ()
    ocr_used: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def record_count(self) -> int:
        """Quantidade de linhas de dados lidas (sem contar o cabeçalho)."""
        return len(self.records)


__all__ = [
    "ExtractionOptions",
    "ExtractionResult",
    "SourceRecord",
]
