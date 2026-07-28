"""Normalizadores de datas, moeda, documentos e telefones."""

from .dates import is_future, parse_date, parse_datetime
from .fields import (
    format_postal_code,
    is_valid_email,
    is_valid_phone,
    is_valid_postal_code,
    normalize_document,
    normalize_email,
    normalize_phone,
    normalize_postal_code,
    normalize_state,
)
from .money import parse_decimal
from .text import (
    clean_text,
    collapse_whitespace,
    lowercase,
    normalize_unicode,
    nullify_markers,
    remove_accents,
    remove_control_characters,
    strip,
    title_case,
    uppercase,
)

__all__ = [
    "clean_text",
    "collapse_whitespace",
    "format_postal_code",
    "is_future",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_postal_code",
    "lowercase",
    "normalize_document",
    "normalize_email",
    "normalize_phone",
    "normalize_postal_code",
    "normalize_state",
    "normalize_unicode",
    "nullify_markers",
    "parse_date",
    "parse_datetime",
    "parse_decimal",
    "remove_accents",
    "remove_control_characters",
    "strip",
    "title_case",
    "uppercase",
]
