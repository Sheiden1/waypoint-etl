"""Adaptadores compartilhados para uploads efêmeros.

As interfaces recebem bytes, mas os casos de uso do Waypoint trabalham com
``Path``. Este módulo faz a ponte sem manter conteúdo enviado após a operação.
"""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePath

from ..application.dto.extraction import ExtractionOptions
from ..application.dto.results import SourcePreview
from ..application.ports.ocr import OcrEngine
from ..application.use_cases.inspect_source import inspect_source

SUPPORTED_UPLOAD_EXTENSIONS: tuple[str, ...] = (
    "csv",
    "xlsx",
    "pdf",
    "docx",
    "txt",
    "png",
    "jpg",
    "jpeg",
)


def safe_upload_name(name: str, *, fallback: str = "upload.bin") -> str:
    """Remove qualquer diretório informado pelo cliente."""
    normalized = name.replace("\\", "/")
    candidate = PurePath(normalized).name.strip()
    return candidate or fallback


def upload_digest(name: str, content: bytes) -> str:
    """Identifica um upload sem persistir seu conteúdo."""
    digest = hashlib.sha256()
    digest.update(safe_upload_name(name).encode("utf-8"))
    digest.update(b"\0")
    digest.update(content)
    return digest.hexdigest()


@contextmanager
def materialized_upload(name: str, content: bytes) -> Iterator[Path]:
    """Materializa bytes em diretório isolado e autodestrutivo."""
    with tempfile.TemporaryDirectory(prefix="waypoint-upload-") as temporary:
        path = Path(temporary) / safe_upload_name(name)
        path.write_bytes(content)
        yield path


def inspect_uploaded_source(
    name: str,
    content: bytes,
    *,
    options: ExtractionOptions | None = None,
    ocr_engine: OcrEngine | None = None,
) -> SourcePreview:
    """Inspeciona um upload usando o mesmo caso de uso da CLI."""
    with materialized_upload(name, content) as source:
        return inspect_source(source, options=options, ocr_engine=ocr_engine)


__all__ = [
    "SUPPORTED_UPLOAD_EXTENSIONS",
    "inspect_uploaded_source",
    "materialized_upload",
    "safe_upload_name",
    "upload_digest",
]
