"""Enums canônicos do domínio."""

from .document_type import DocumentType
from .entity_type import EntityType
from .invoice_status import InvoiceStatus
from .issue_severity import IssueSeverity
from .run_status import RunStatus
from .source_format import SourceFormat

__all__ = [
    "DocumentType",
    "EntityType",
    "InvoiceStatus",
    "IssueSeverity",
    "RunStatus",
    "SourceFormat",
]
