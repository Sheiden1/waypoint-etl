"""Validadores de schema e severidades."""

from .entities import validate_record, validate_records
from .result import CanonicalEntity, ValidatedRecord

__all__ = [
    "CanonicalEntity",
    "ValidatedRecord",
    "validate_record",
    "validate_records",
]
