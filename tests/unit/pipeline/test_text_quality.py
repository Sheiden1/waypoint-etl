"""Testes da heurística que decide se o OCR é necessário (seção 12)."""

from __future__ import annotations

import pytest

from waypoint_etl.pipeline.cleaners.text_quality import (
    MIN_CHARACTERS,
    assess_text,
)

FICHA = """FICHA CADASTRAL DE CLIENTE
Nome: Ana Maria Silva
CPF/CNPJ: 390.533.447-05
E-mail: ana@exemplo.com.br
"""


def test_empty_text_is_insufficient() -> None:
    quality = assess_text("")

    assert quality.character_count == 0
    assert not quality.is_sufficient


def test_whitespace_only_is_insufficient() -> None:
    assert not assess_text("   \n\n  ").is_sufficient


def test_long_alphanumeric_text_is_sufficient() -> None:
    quality = assess_text("a" * (MIN_CHARACTERS + 10))

    assert quality.is_sufficient
    assert quality.alphanumeric_ratio == 1.0


def test_short_text_without_patterns_is_insufficient() -> None:
    quality = assess_text("Pagina 1")

    assert not quality.is_sufficient
    assert "muito curto" in quality.reason


def test_symbol_noise_is_insufficient() -> None:
    """PDF escaneado mal extraído devolve ruído de símbolos, não texto."""
    quality = assess_text("#$%&*(){}[]<>|\\/~^`" * 5)

    assert not quality.is_sufficient
    assert "alfanumérica" in quality.reason


def test_short_text_with_a_recognized_pattern_is_sufficient() -> None:
    """Um CPF legível vale mais que uma página de ruído."""
    quality = assess_text("CPF 390.533.447-05")

    assert quality.character_count < MIN_CHARACTERS
    assert quality.has_expected_patterns
    assert quality.is_sufficient
    assert "padrões esperados" in quality.reason


@pytest.mark.parametrize(
    "text",
    [
        "E-mail: ana@exemplo.com.br",
        "Cadastro 15/03/2024",
        "CEP 01310-100",
        "CNPJ 11.222.333/0001-81",
    ],
)
def test_any_expected_pattern_makes_it_sufficient(text: str) -> None:
    assert assess_text(text).is_sufficient


def test_realistic_form_is_sufficient() -> None:
    quality = assess_text(FICHA)

    assert quality.is_sufficient
    assert quality.has_expected_patterns


def test_reason_is_readable_for_the_audit_report() -> None:
    assert assess_text("x").reason.startswith("texto muito curto")
