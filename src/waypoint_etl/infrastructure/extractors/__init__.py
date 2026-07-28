"""Extractors de CSV, Excel, PDF, DOCX, TXT e imagens."""

from .csv_extractor import CsvExtractor
from .excel_extractor import ExcelExtractor
from .registry import EXTENSION_FORMATS, detect_format, get_extractor

__all__ = [
    "EXTENSION_FORMATS",
    "CsvExtractor",
    "ExcelExtractor",
    "detect_format",
    "get_extractor",
]
