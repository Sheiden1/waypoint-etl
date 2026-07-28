"""Port de OCR implementado pela infraestrutura.

Manter o OCR atrás de uma interface permite testar toda a lógica de fallback
com um motor falso e determinístico, sem depender do binário do Tesseract.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class OcrEngine(Protocol):
    """Converte a imagem de uma página em texto."""

    @property
    def name(self) -> str:
        """Identificação do motor, registrada na auditoria."""
        ...

    def is_available(self) -> bool:
        """Indica se o motor pode ser usado neste ambiente."""
        ...

    def image_to_text(self, image: bytes) -> str:
        """Extrai texto de uma imagem codificada em PNG."""
        ...


__all__ = ["OcrEngine"]
