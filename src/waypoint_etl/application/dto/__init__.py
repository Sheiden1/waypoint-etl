"""Objetos de transferência de dados entre camadas."""

from .document import PAGE_SEPARATOR, DocumentText, PageText
from .extraction import ExtractionOptions, ExtractionResult, SourceRecord
from .migration import MigrationRun, compute_file_hash

__all__ = [
    "PAGE_SEPARATOR",
    "DocumentText",
    "ExtractionOptions",
    "ExtractionResult",
    "MigrationRun",
    "PageText",
    "SourceRecord",
    "compute_file_hash",
]
