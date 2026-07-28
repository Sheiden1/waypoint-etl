"""Fallback automático para OCR quando o texto nativo é insuficiente.

Implementado como um **decorador** de ``DocumentExtractor``: o ``PdfExtractor``
continua fazendo só a extração nativa, e quem quiser OCR embrulha o extrator.
Isso mantém o extrator testável sem Tesseract e deixa a decisão de custo
(renderizar páginas é caro) explícita em quem monta o pipeline.

Segue a estratégia da seção 12: tenta o texto nativo, mede a qualidade e só
então recorre ao OCR, sempre registrando que o usou.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from ...application.dto.document import DocumentText, PageText
from ...application.dto.extraction import ExtractionOptions
from ...application.ports.extractor import DocumentExtractor
from ...application.ports.ocr import OcrEngine
from ...domain.enums.source_format import SourceFormat
from ...pipeline.cleaners.text_quality import assess_text

# 300 DPI é o padrão recomendado para OCR de texto impresso: abaixo disso a
# taxa de erro sobe muito; acima, o ganho não paga o custo de memória.
OCR_RENDER_DPI = 300


class DocumentExtractorWithOcr:
    """Decora um extrator de documentos acrescentando fallback para OCR."""

    def __init__(
        self,
        extractor: DocumentExtractor,
        engine: OcrEngine,
        *,
        dpi: int = OCR_RENDER_DPI,
    ) -> None:
        self._extractor = extractor
        self._engine = engine
        self._dpi = dpi

    @property
    def source_format(self) -> SourceFormat:
        return self._extractor.source_format

    def supports(self, path: Path) -> bool:
        return self._extractor.supports(path)

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        """Extrai o texto, aplicando OCR apenas nas páginas que precisarem."""
        native = self._extractor.extract_text(path, options)

        insufficient = [
            page for page in native.pages if not assess_text(page.text).is_sufficient
        ]
        if not insufficient:
            return native

        if not self._engine.is_available():
            return _with_warning(
                native,
                f"{len(insufficient)} página(s) sem texto aproveitável, mas o "
                "OCR não está disponível neste ambiente. Instale o Tesseract "
                "para processar documentos escaneados.",
            )

        if native.source_format is not SourceFormat.PDF:
            return native

        return self._apply_ocr(path, native, {page.number for page in insufficient})

    def _apply_ocr(
        self, path: Path, native: DocumentText, targets: set[int]
    ) -> DocumentText:
        """Renderiza e aplica OCR nas páginas indicadas."""
        pages: list[PageText] = []
        recovered: list[int] = []
        failed: list[int] = []

        with pymupdf.open(path) as document:
            for page in native.pages:
                if page.number not in targets:
                    pages.append(page)
                    continue

                text = self._ocr_page(document, page.number)
                if text is None:
                    failed.append(page.number)
                    pages.append(page)
                    continue

                recovered.append(page.number)
                pages.append(PageText(number=page.number, text=text))

        return DocumentText(
            source_name=native.source_name,
            source_format=native.source_format,
            pages=tuple(pages),
            ocr_used=bool(recovered),
            warnings=native.warnings + _ocr_warnings(recovered, failed),
        )

    def _ocr_page(self, document: pymupdf.Document, number: int) -> str | None:
        """Renderiza uma página e devolve o texto reconhecido.

        Uma página que falhe no OCR não interrompe as demais (seção 17).
        """
        try:
            page = document[number - 1]
            pixmap = page.get_pixmap(dpi=self._dpi)
            text = self._engine.image_to_text(pixmap.tobytes("png"))
        except Exception:
            return None
        return text if text.strip() else None


def _ocr_warnings(recovered: list[int], failed: list[int]) -> tuple[str, ...]:
    """Registra no relatório o que o OCR recuperou e o que não (seção 12)."""
    warnings: list[str] = []
    if recovered:
        listed = ", ".join(str(number) for number in recovered)
        warnings.append(
            f"OCR aplicado na(s) página(s) {listed}. Confira os valores "
            "reconhecidos: texto de OCR não é confiável sem revisão."
        )
    if failed:
        listed = ", ".join(str(number) for number in failed)
        warnings.append(
            f"OCR não conseguiu extrair texto da(s) página(s) {listed}."
        )
    return tuple(warnings)


def _with_warning(document: DocumentText, message: str) -> DocumentText:
    """Devolve o documento com um aviso adicional."""
    return DocumentText(
        source_name=document.source_name,
        source_format=document.source_format,
        pages=document.pages,
        ocr_used=document.ocr_used,
        warnings=(*document.warnings, message),
    )


__all__ = ["OCR_RENDER_DPI", "DocumentExtractorWithOcr"]
