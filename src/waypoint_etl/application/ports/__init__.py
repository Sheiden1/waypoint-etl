"""Interfaces (ports) implementadas pela infraestrutura."""

from .extractor import DocumentExtractor, TabularExtractor
from .ocr import OcrEngine

__all__ = ["DocumentExtractor", "OcrEngine", "TabularExtractor"]
