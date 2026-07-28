"""Heurística de qualidade do texto extraído (seção 12).

Decide se a extração nativa foi suficiente ou se vale tentar OCR. A heurística
é deliberadamente simples e explicável: três sinais somados, nenhum modelo.

Ela nunca afirma que o texto está *correto* — apenas que há texto aproveitável.
Resultado de OCR continua passando pela validação (seção 12, item 7).
"""

from __future__ import annotations

from dataclasses import dataclass

from .patterns import (
    find_dates,
    find_documents,
    find_emails,
    find_phones,
    find_postal_codes,
)

# Abaixo disso a página quase certamente é uma imagem com um rótulo solto.
MIN_CHARACTERS = 40

# PDFs escaneados sem camada de texto costumam devolver ruído de símbolos;
# texto real de cadastro é majoritariamente alfanumérico.
MIN_ALPHANUMERIC_RATIO = 0.5


@dataclass(frozen=True, slots=True)
class TextQuality:
    """Avaliação de um trecho de texto extraído."""

    character_count: int
    alphanumeric_ratio: float
    has_expected_patterns: bool

    @property
    def is_sufficient(self) -> bool:
        """Indica que a extração nativa basta e o OCR é desnecessário.

        Encontrar um padrão esperado (CPF, e-mail, data...) vale por si só: um
        texto curto mas com um CPF legível é mais útil do que uma página longa
        de ruído.
        """
        if self.has_expected_patterns:
            return True
        return (
            self.character_count >= MIN_CHARACTERS
            and self.alphanumeric_ratio >= MIN_ALPHANUMERIC_RATIO
        )

    @property
    def reason(self) -> str:
        """Explicação legível da decisão, para o relatório de auditoria."""
        if self.has_expected_patterns:
            return "padrões esperados encontrados no texto nativo"
        if self.character_count < MIN_CHARACTERS:
            return (
                f"texto muito curto ({self.character_count} caracteres, "
                f"mínimo {MIN_CHARACTERS})"
            )
        if self.alphanumeric_ratio < MIN_ALPHANUMERIC_RATIO:
            return (
                f"proporção alfanumérica baixa ({self.alphanumeric_ratio:.0%}, "
                f"mínimo {MIN_ALPHANUMERIC_RATIO:.0%})"
            )
        return "texto nativo suficiente"


def assess_text(text: str) -> TextQuality:
    """Avalia a qualidade de um texto extraído nativamente."""
    stripped = text.strip()
    return TextQuality(
        character_count=len(stripped),
        alphanumeric_ratio=_alphanumeric_ratio(stripped),
        has_expected_patterns=_has_expected_patterns(stripped),
    )


def _alphanumeric_ratio(text: str) -> float:
    """Proporção de caracteres alfanuméricos, ignorando espaços."""
    meaningful = [char for char in text if not char.isspace()]
    if not meaningful:
        return 0.0
    alphanumeric = sum(1 for char in meaningful if char.isalnum())
    return alphanumeric / len(meaningful)


def _has_expected_patterns(text: str) -> bool:
    """Indica se o texto contém algum dado que o pipeline sabe aproveitar."""
    if not text:
        return False
    finders = (
        find_documents,
        find_emails,
        find_dates,
        find_postal_codes,
        find_phones,
    )
    return any(finder(text) for finder in finders)


__all__ = [
    "MIN_ALPHANUMERIC_RATIO",
    "MIN_CHARACTERS",
    "TextQuality",
    "assess_text",
]
