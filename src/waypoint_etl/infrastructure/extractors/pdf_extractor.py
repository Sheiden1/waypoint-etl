"""Extrator de PDFs com camada de texto ("PDF digital").

Este extrator faz apenas a primeira etapa da estratégia da seção 12: tentar o
texto nativo. Ele nunca executa OCR — apenas registra, por página, o que veio
vazio, para que o estágio de OCR (Dia 8) decida o fallback com base em
``DocumentText.empty_pages``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect

from ...application.dto.document import DocumentText, PageText
from ...application.dto.extraction import ExtractionOptions
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import ExtractionError
from .base import ensure_readable_file

SUPPORTED_SUFFIXES = frozenset({".pdf"})


class PdfExtractor:
    """Lê o texto nativo de um PDF, página a página."""

    @property
    def source_format(self) -> SourceFormat:
        return SourceFormat.PDF

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        ensure_readable_file(path)

        with _open_pdf(path) as pdf:
            pages = tuple(_iter_pages(pdf, path))

        document = DocumentText(
            source_name=path.name,
            source_format=SourceFormat.PDF,
            pages=pages,
            warnings=_build_warnings(pages),
        )
        return document


def _open_pdf(path: Path) -> Any:
    """Abre o PDF, traduzindo falhas de leitura para um erro controlado."""
    try:
        return pdfplumber.open(path)
    except Exception as error:
        if _is_password_error(error):
            raise ExtractionError(
                f"'{path.name}' está protegido por senha. "
                "Remova a proteção antes de enviar o arquivo."
            ) from error
        # O pdfminer sinaliza arquivo inválido de várias formas (PSException,
        # struct.error, TypeError); todas viram a mesma falha controlada.
        raise ExtractionError(
            f"Não foi possível ler '{path.name}': o arquivo não parece ser um "
            "PDF válido ou está corrompido."
        ) from error


def _is_password_error(error: BaseException) -> bool:
    """Indica se a falha foi causada por proteção com senha.

    O pdfplumber embrulha as exceções do pdfminer (``PdfminerException``), então
    a causa real pode estar na cadeia de ``__cause__`` ou nos argumentos.
    """
    if isinstance(error, PDFPasswordIncorrect):
        return True
    if error.__cause__ is not None and _is_password_error(error.__cause__):
        return True
    return any(
        isinstance(arg, BaseException) and _is_password_error(arg)
        for arg in error.args
    )


def _iter_pages(pdf: Any, path: Path) -> Iterator[PageText]:
    """Extrai o texto de cada página.

    Uma página problemática vira página vazia (candidata a OCR) em vez de
    interromper a leitura das demais (seção 17).
    """
    for number, page in enumerate(pdf.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            # Página malformada não derruba a leitura das demais.
            text = ""
        finally:
            # Libera os caches por página: PDFs grandes crescem sem isso.
            page.flush_cache()
        yield PageText(number=number, text=text)

    if not pdf.pages:
        raise ExtractionError(
            f"'{path.name}' não possui páginas legíveis. "
            "Verifique se o arquivo foi exportado corretamente."
        )


def _build_warnings(pages: tuple[PageText, ...]) -> tuple[str, ...]:
    """Descreve as páginas sem camada de texto, sem decidir pelo OCR."""
    empty = [page.number for page in pages if page.is_empty]
    if not empty:
        return ()
    if len(empty) == len(pages):
        return (
            "Nenhuma página possui camada de texto: o documento provavelmente "
            "foi escaneado e precisará de OCR.",
        )
    listed = ", ".join(str(number) for number in empty)
    return (f"Páginas sem camada de texto: {listed}. Podem precisar de OCR.",)


__all__ = ["SUPPORTED_SUFFIXES", "PdfExtractor"]
