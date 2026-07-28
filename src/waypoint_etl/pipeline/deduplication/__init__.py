"""Estratégias de deduplicação."""

from .detector import (
    NAME_SIMILARITY_THRESHOLD,
    DeduplicationResult,
    DuplicateMatch,
    annotate_duplicates,
    find_duplicates,
)

__all__ = [
    "NAME_SIMILARITY_THRESHOLD",
    "DeduplicationResult",
    "DuplicateMatch",
    "annotate_duplicates",
    "find_duplicates",
]
