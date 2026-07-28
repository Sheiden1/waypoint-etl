"""Detecção do formato de origem e seleção do extrator correspondente."""

from __future__ import annotations

from pathlib import Path

from ...application.ports.extractor import Extractor
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import UnsupportedFormatError
from .csv_extractor import CsvExtractor
from .excel_extractor import ExcelExtractor

# Formatos declarados no escopo do MVP (seção 4), mesmo os ainda não
# implementados: a detecção precisa distinguir "não suportado" de "pendente".
EXTENSION_FORMATS: dict[str, SourceFormat] = {
    ".csv": SourceFormat.CSV,
    ".xlsx": SourceFormat.EXCEL,
    ".xlsm": SourceFormat.EXCEL,
    ".pdf": SourceFormat.PDF,
    ".docx": SourceFormat.DOCX,
    ".txt": SourceFormat.TXT,
    ".png": SourceFormat.IMAGE,
    ".jpg": SourceFormat.IMAGE,
    ".jpeg": SourceFormat.IMAGE,
}


def _build_extractors() -> tuple[Extractor, ...]:
    """Extratores disponíveis, na ordem de tentativa."""
    return (CsvExtractor(), ExcelExtractor())


def detect_format(path: Path) -> SourceFormat:
    """Identifica o formato pela extensão do arquivo.

    Levanta ``UnsupportedFormatError`` quando a extensão está fora do escopo.
    """
    suffix = path.suffix.lower()
    try:
        return EXTENSION_FORMATS[suffix]
    except KeyError:
        supported = ", ".join(sorted(EXTENSION_FORMATS))
        raise UnsupportedFormatError(
            f"Formato não suportado: '{suffix or path.name}'. "
            f"Extensões aceitas: {supported}."
        ) from None


def get_extractor(path: Path) -> Extractor:
    """Devolve o extrator capaz de ler ``path``.

    Formatos previstos no MVP mas ainda não implementados falham com uma
    mensagem explícita, nunca com um resultado simulado.
    """
    source_format = detect_format(path)
    for extractor in _build_extractors():
        if extractor.supports(path):
            return extractor
    raise UnsupportedFormatError(
        f"O formato '{source_format.value}' ainda não possui extrator "
        "implementado nesta versão do Waypoint."
    )


__all__ = ["EXTENSION_FORMATS", "detect_format", "get_extractor"]
