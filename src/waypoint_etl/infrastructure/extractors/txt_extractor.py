"""Extrator de arquivos de texto puro exportados por sistemas antigos."""

from __future__ import annotations

from pathlib import Path

from ...application.dto.document import DocumentText, PageText
from ...application.dto.extraction import ExtractionOptions
from ...domain.enums.source_format import SourceFormat
from .base import ENCODING_CANDIDATES, ensure_readable_file, read_text_file

SUPPORTED_SUFFIXES = frozenset({".txt"})


class TxtExtractor:
    """Lê arquivos ``.txt`` detectando a codificação, como no extrator de CSV."""

    @property
    def source_format(self) -> SourceFormat:
        return SourceFormat.TXT

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def extract_text(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> DocumentText:
        opts = options or ExtractionOptions()
        ensure_readable_file(path)

        warnings: list[str] = []
        text, encoding = read_text_file(path, opts.encoding)
        if opts.encoding is None and encoding != ENCODING_CANDIDATES[0]:
            warnings.append(
                f"Arquivo lido com a codificação '{encoding}'. "
                "Informe a codificação no template se algum acento estiver errado."
            )
        if not text.strip():
            warnings.append("O arquivo não possui texto aproveitável.")

        return DocumentText(
            source_name=path.name,
            source_format=SourceFormat.TXT,
            # Texto puro não tem paginação: todo o conteúdo é uma página só.
            pages=(PageText(number=1, text=text),),
            warnings=tuple(warnings),
        )


__all__ = ["SUPPORTED_SUFFIXES", "TxtExtractor"]
