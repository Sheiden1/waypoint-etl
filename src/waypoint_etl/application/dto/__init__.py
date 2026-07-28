"""Objetos de transferência de dados entre camadas."""

from .document import PAGE_SEPARATOR, DocumentText, PageText
from .extraction import ExtractionOptions, ExtractionResult, SourceRecord

__all__ = [
    "PAGE_SEPARATOR",
    "DocumentText",
    "ExtractionOptions",
    "ExtractionResult",
    "PageText",
    "SourceRecord",
]
