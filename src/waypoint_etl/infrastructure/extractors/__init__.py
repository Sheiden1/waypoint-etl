"""Extractors de CSV, Excel, PDF, DOCX, TXT e imagens."""

from .csv_extractor import CsvExtractor
from .docx_extractor import DocxExtractor
from .excel_extractor import ExcelExtractor
from .pdf_extractor import PdfExtractor
from .registry import (
    DOCUMENT_FORMATS,
    EXTENSION_FORMATS,
    TABULAR_FORMATS,
    detect_format,
    get_document_extractor,
    get_tabular_extractor,
    is_tabular,
)
from .txt_extractor import TxtExtractor

__all__ = [
    "DOCUMENT_FORMATS",
    "EXTENSION_FORMATS",
    "TABULAR_FORMATS",
    "CsvExtractor",
    "DocxExtractor",
    "ExcelExtractor",
    "PdfExtractor",
    "TxtExtractor",
    "detect_format",
    "get_document_extractor",
    "get_tabular_extractor",
    "is_tabular",
]
