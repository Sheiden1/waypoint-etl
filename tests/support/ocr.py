"""Dublês do motor de OCR.

Permitem testar toda a lógica de fallback de forma determinística, sem depender
do binário do Tesseract estar instalado (seção 19: testes determinísticos e sem
dependência externa).
"""

from __future__ import annotations

OCR_TEXT = "Nome: Ana Maria Silva\nCPF/CNPJ: 390.533.447-05"


class FakeOcrEngine:
    """Motor de OCR que devolve sempre o mesmo texto."""

    def __init__(self, *, text: str = OCR_TEXT, available: bool = True) -> None:
        self._text = text
        self._available = available
        self.calls = 0

    @property
    def name(self) -> str:
        return "fake"

    def is_available(self) -> bool:
        return self._available

    def image_to_text(self, image: bytes) -> str:
        self.calls += 1
        return self._text


class BrokenOcrEngine(FakeOcrEngine):
    """Motor que sempre falha, para checar a degradação controlada."""

    def image_to_text(self, image: bytes) -> str:
        self.calls += 1
        raise RuntimeError("falha do motor de OCR")


__all__ = ["OCR_TEXT", "BrokenOcrEngine", "FakeOcrEngine"]
