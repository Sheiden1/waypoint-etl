"""Objetos de transferência de dados entre camadas."""

from .document import PAGE_SEPARATOR, DocumentText, PageText
from .extraction import ExtractionOptions, ExtractionResult, SourceRecord
from .migration import MigrationRun, compute_file_hash
from .results import MigrationResult, SourcePreview, StageDuration, StageTimer

__all__ = [
    "PAGE_SEPARATOR",
    "DocumentText",
    "ExtractionOptions",
    "ExtractionResult",
    "MigrationResult",
    "MigrationRun",
    "PageText",
    "SourcePreview",
    "SourceRecord",
    "StageDuration",
    "StageTimer",
    "compute_file_hash",
]
