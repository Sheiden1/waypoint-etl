"""Extrator de imagens (``.png``, ``.jpg``, ``.jpeg``) via OCR.

Imagem não tem camada de texto: aqui o OCR não é fallback, é o único caminho.
Por isso este extrator recebe o motor no construtor, em vez de decorar outro.
"""

from __future__ import annotations

from pathlib import Path

from ...application.dto.document import DocumentText, PageText
from ...application.dto.extraction import ExtractionOptions
from ...application.ports.ocr import OcrEngine
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import ExtractionError
from .base import ensure_readable_file

SUPPORTED_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})


class ImageExtractor:
    """Lê o texto de uma imagem usando OCR."""

    def __init__(self, engine: OcrEngine) -> None:
        self._engine = engine

    @property
    def source_format(self) -> SourceFormat:
        return SourceFormat.IMAGE

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        ensure_readable_file(path)

        if not self._engine.is_available():
            raise ExtractionError(
                f"'{path.name}' é uma imagem e exige OCR, mas o Tesseract não "
                "está disponível neste ambiente. Instale o binário ou aponte "
                "TESSERACT_CMD no .env."
            )

        try:
            text = self._engine.image_to_text(path.read_bytes())
        except ExtractionError:
            raise
        except Exception as error:
            raise ExtractionError(
                f"Não foi possível processar a imagem '{path.name}': o arquivo "
                "pode estar corrompido ou em um formato não suportado."
            ) from error

        warnings = (
            "Conteúdo obtido por OCR: confira os valores reconhecidos antes de "
            "importar.",
        )
        if not text.strip():
            warnings = (
                "O OCR não reconheceu nenhum texto nesta imagem. Verifique a "
                "resolução e o contraste do arquivo.",
            )

        return DocumentText(
            source_name=path.name,
            source_format=SourceFormat.IMAGE,
            pages=(PageText(number=1, text=text),),
            ocr_used=True,
            warnings=warnings,
        )


__all__ = ["SUPPORTED_SUFFIXES", "ImageExtractor"]
