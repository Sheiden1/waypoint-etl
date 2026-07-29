"""Estruturação de documentos textuais em registros canônicos."""

from .records import DocumentStructureError, parse_document_records

__all__ = ["DocumentStructureError", "parse_document_records"]
