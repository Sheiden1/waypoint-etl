"""Tipo de documento fiscal brasileiro."""

from __future__ import annotations

from enum import StrEnum


class DocumentType(StrEnum):
    """Tipo de documento identificado a partir da quantidade de dígitos."""

    CPF = "cpf"
    CNPJ = "cnpj"
