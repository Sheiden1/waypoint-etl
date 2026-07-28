"""Extrator de arquivos CSV.

Usa a biblioteca padrão: o ``csv`` resolve o problema com clareza equivalente à
do Pandas e mantém o controle sobre a numeração das linhas de origem.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator, Sequence
from pathlib import Path

from ...application.dto.extraction import (
    ExtractionOptions,
    ExtractionResult,
    SourceRecord,
)
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import EmptySourceError, ExtractionError
from .base import (
    build_row_mapping,
    coerce_cell,
    ensure_readable_file,
    is_blank_row,
    normalize_headers,
)

SUPPORTED_SUFFIXES = frozenset({".csv"})

# Ordem de tentativa: exportações de ERPs legados costumam vir em UTF-8 (com ou
# sem BOM) ou em codificações Windows. ``latin-1`` nunca falha e fecha a lista.
ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

_SNIFF_DELIMITERS = ",;\t|"
_SNIFF_BYTES = 8192


class CsvExtractor:
    """Lê arquivos ``.csv`` com detecção de codificação e delimitador."""

    @property
    def source_format(self) -> SourceFormat:
        return SourceFormat.CSV

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_SUFFIXES

    def extract(
        self, path: Path, options: ExtractionOptions | None = None
    ) -> ExtractionResult:
        opts = options or ExtractionOptions()
        ensure_readable_file(path)

        warnings: list[str] = []
        text, encoding = _read_text(path, opts.encoding)
        if opts.encoding is None and encoding != ENCODING_CANDIDATES[0]:
            warnings.append(
                f"Arquivo lido com a codificação '{encoding}'. "
                "Informe a codificação no template se algum acento estiver errado."
            )

        delimiter = opts.delimiter or _sniff_delimiter(text)
        rows = _iter_rows(text, delimiter)
        header, warnings_from_header = _read_header(rows, opts.header_row, path)
        warnings.extend(warnings_from_header)

        records: list[SourceRecord] = []
        for row_number, raw_values in rows:
            values = [coerce_cell(value) for value in raw_values]
            if is_blank_row(values):
                continue
            records.append(
                SourceRecord(
                    row_number=row_number,
                    values=build_row_mapping(header, values),
                )
            )

        return ExtractionResult(
            source_name=path.name,
            source_format=SourceFormat.CSV,
            columns=header,
            records=tuple(records),
            warnings=tuple(warnings),
        )


def _read_text(path: Path, encoding: str | None) -> tuple[str, str]:
    """Lê o arquivo como texto, devolvendo ``(conteúdo, codificação usada)``."""
    candidates = (encoding,) if encoding else ENCODING_CANDIDATES
    last_error: UnicodeDecodeError | None = None
    for candidate in candidates:
        try:
            return path.read_text(encoding=candidate), candidate
        except UnicodeDecodeError as error:
            last_error = error
        except LookupError as error:
            raise ExtractionError(
                f"Codificação desconhecida: '{candidate}'. "
                "Use um nome válido, como 'utf-8' ou 'cp1252'."
            ) from error
    raise ExtractionError(
        f"Não foi possível decodificar '{path.name}'. "
        "Informe a codificação correta no template De/Para."
    ) from last_error


def _sniff_delimiter(text: str) -> str:
    """Detecta o delimitador; assume vírgula quando a amostra é inconclusiva."""
    sample = text[:_SNIFF_BYTES]
    if not sample.strip():
        return ","
    try:
        return csv.Sniffer().sniff(sample, delimiters=_SNIFF_DELIMITERS).delimiter
    except csv.Error:
        return ","


def _iter_rows(text: str, delimiter: str) -> Iterator[tuple[int, list[str]]]:
    """Itera ``(número da linha no arquivo, células)`` respeitando aspas.

    O buffer usa ``newline=""`` para que quebras de linha dentro de campos entre
    aspas sejam preservadas, enquanto ``line_num`` continua contando as linhas
    físicas do arquivo.
    """
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    for row in reader:
        yield reader.line_num, row


def _read_header(
    rows: Iterator[tuple[int, Sequence[str]]], header_row: int, path: Path
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Consome as linhas até o cabeçalho e o devolve normalizado."""
    if header_row < 1:
        raise ExtractionError(
            f"header_row deve ser maior ou igual a 1 (recebido: {header_row})."
        )

    for _ in range(header_row - 1):
        if next(rows, None) is None:
            raise EmptySourceError(
                f"'{path.name}' tem menos de {header_row} linhas: "
                "o cabeçalho configurado não existe."
            )

    current = next(rows, None)
    if current is None:
        raise EmptySourceError(
            f"'{path.name}' não possui a linha de cabeçalho {header_row}."
        )

    _, raw_header = current
    header, warnings = normalize_headers(raw_header)
    if not header:
        raise EmptySourceError(f"O cabeçalho de '{path.name}' está vazio.")
    return header, warnings


__all__ = ["ENCODING_CANDIDATES", "SUPPORTED_SUFFIXES", "CsvExtractor"]
