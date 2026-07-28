"""Formato do arquivo de origem detectado na etapa de extração."""

from __future__ import annotations

from enum import StrEnum


class SourceFormat(StrEnum):
    """Formatos de entrada suportados pelo MVP (seção 4 do CLAUDE.md)."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
