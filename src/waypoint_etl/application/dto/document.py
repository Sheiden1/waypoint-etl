"""Contratos da extração de documentos textuais (TXT, DOCX, PDF).

Documentos não têm linhas e colunas como uma planilha: a estruturação em
registros acontece depois, por Regex (seção 11). Por isso a extração de
documentos devolve texto por página, e não ``SourceRecord``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.enums.source_format import SourceFormat

PAGE_SEPARATOR = "\n\n"


@dataclass(frozen=True, slots=True)
class PageText:
    """Texto de uma página (ou bloco) do documento.

    Formatos sem paginação (TXT, DOCX) devolvem uma única página de número 1.
    """

    number: int
    text: str

    @property
    def character_count(self) -> int:
        """Quantidade de caracteres da página, sem espaços nas pontas."""
        return len(self.text.strip())

    @property
    def is_empty(self) -> bool:
        """Indica que a página não trouxe texto aproveitável."""
        return self.character_count == 0


@dataclass(frozen=True, slots=True)
class DocumentText:
    """Texto extraído de um documento, preservando a divisão por página.

    A contagem por página permite que o estágio de OCR (seção 12) decida se a
    extração nativa foi suficiente sem precisar reabrir o arquivo.
    """

    source_name: str
    source_format: SourceFormat
    pages: tuple[PageText, ...]
    ocr_used: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def text(self) -> str:
        """Texto completo do documento, com as páginas separadas."""
        return PAGE_SEPARATOR.join(
            page.text for page in self.pages if not page.is_empty
        )

    @property
    def page_count(self) -> int:
        """Quantidade de páginas lidas."""
        return len(self.pages)

    @property
    def character_count(self) -> int:
        """Total de caracteres aproveitáveis do documento."""
        return sum(page.character_count for page in self.pages)

    @property
    def empty_pages(self) -> tuple[int, ...]:
        """Números das páginas sem texto — candidatas a OCR no Dia 8."""
        return tuple(page.number for page in self.pages if page.is_empty)

    @property
    def is_empty(self) -> bool:
        """Indica que nenhuma página trouxe texto."""
        return self.character_count == 0


__all__ = ["PAGE_SEPARATOR", "DocumentText", "PageText"]
