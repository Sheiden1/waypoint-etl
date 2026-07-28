"""Integração com o Tesseract real (seção 26: "OCR executado de verdade").

Estes testes são pulados quando o binário do Tesseract não está instalado, para
que a suíte continue determinística e sem dependência externa (seção 19). Eles
são o que comprova o requisito da seção 26 — rode-os em um ambiente com o
Tesseract instalado (o Dockerfile do Dia 11 o inclui)::

    uv run pytest tests/integration/test_ocr_tesseract.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from waypoint_etl.demo.document_files import (
    write_scanned_form_image,
    write_scanned_form_pdf,
)
from waypoint_etl.infrastructure.extractors.image_extractor import ImageExtractor
from waypoint_etl.infrastructure.extractors.pdf_extractor import PdfExtractor
from waypoint_etl.infrastructure.ocr.fallback import DocumentExtractorWithOcr
from waypoint_etl.infrastructure.ocr.tesseract import TesseractEngine
from waypoint_etl.pipeline.cleaners.patterns import find_cpfs

_ENGINE = TesseractEngine()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _ENGINE.is_available(),
        reason="Tesseract OCR não está instalado neste ambiente",
    ),
]


def test_reads_text_from_a_scanned_image(tmp_path: Path) -> None:
    source = write_scanned_form_image(tmp_path / "ficha.png")

    result = ImageExtractor(_ENGINE).extract_text(source)

    assert result.ocr_used is True
    assert not result.is_empty
    assert "FICHA" in result.text.upper()


def test_scanned_pdf_falls_back_to_ocr(tmp_path: Path) -> None:
    """O caminho completo da seção 12: nativo vazio -> heurística -> OCR."""
    source = write_scanned_form_pdf(tmp_path / "escaneada.pdf", count=1)

    native = PdfExtractor().extract_text(source)
    result = DocumentExtractorWithOcr(PdfExtractor(), _ENGINE).extract_text(source)

    assert native.is_empty, "o fixture precisa ser um PDF sem camada de texto"
    assert result.ocr_used is True
    assert result.character_count > native.character_count


def test_ocr_recovers_a_document_number(tmp_path: Path) -> None:
    """O que importa não é o texto perfeito, e sim o dado aproveitável."""
    source = write_scanned_form_image(tmp_path / "ficha.png")

    result = ImageExtractor(_ENGINE).extract_text(source)

    assert find_cpfs(result.text) or find_cpfs(result.text.replace(" ", "")), (
        "o CPF da ficha deveria ser reconhecido pelo OCR"
    )
