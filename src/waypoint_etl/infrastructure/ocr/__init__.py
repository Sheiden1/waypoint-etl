"""Integração de OCR (Tesseract) e pré-processamento."""

from .fallback import OCR_RENDER_DPI, DocumentExtractorWithOcr
from .preprocessing import PreprocessingOptions, preprocess
from .tesseract import OcrUnavailableError, TesseractEngine

__all__ = [
    "OCR_RENDER_DPI",
    "DocumentExtractorWithOcr",
    "OcrUnavailableError",
    "PreprocessingOptions",
    "TesseractEngine",
    "preprocess",
]
