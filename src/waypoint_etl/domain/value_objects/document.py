"""Documento fiscal brasileiro (CPF/CNPJ) como value object.

Inclui validação dos dígitos verificadores e mascaramento para uso em mensagens
de auditoria apresentadas na interface (seção 18: mascarar CPF/CNPJ).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..enums.document_type import DocumentType
from ..errors import InvalidDocumentError

_NON_DIGIT = re.compile(r"\D")

CPF_LENGTH = 11
CNPJ_LENGTH = 14


def only_digits(raw: str | None) -> str:
    """Remove tudo que não for dígito."""
    return _NON_DIGIT.sub("", raw or "")


def is_valid_cpf(value: str) -> bool:
    """Valida um CPF pelos dígitos verificadores.

    Aceita valor com ou sem máscara. Rejeita sequências repetidas (ex.: todos
    os dígitos iguais), que passam na fórmula mas não são CPFs válidos.
    """
    digits = only_digits(value)
    if len(digits) != CPF_LENGTH or not digits.isdigit():
        return False
    if digits == digits[0] * CPF_LENGTH:
        return False

    for length in (9, 10):
        total = sum(
            int(digits[i]) * ((length + 1) - i) for i in range(length)
        )
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if check != int(digits[length]):
            return False
    return True


def is_valid_cnpj(value: str) -> bool:
    """Valida um CNPJ pelos dígitos verificadores.

    Aceita valor com ou sem máscara. Rejeita sequências de dígitos repetidos.
    """
    digits = only_digits(value)
    if len(digits) != CNPJ_LENGTH or not digits.isdigit():
        return False
    if digits == digits[0] * CNPJ_LENGTH:
        return False

    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_second = [6, *weights_first]

    for weights, length in ((weights_first, 12), (weights_second, 13)):
        total = sum(int(digits[i]) * weights[i] for i in range(length))
        remainder = total % 11
        check = 0 if remainder < 2 else 11 - remainder
        if check != int(digits[length]):
            return False
    return True


def mask_document(value: str) -> str:
    """Mascara um documento para exibição, preservando apenas parte dos dígitos.

    Ex.: CPF ``11144477735`` -> ``111.***.***-35``. Nunca deve expor o documento
    completo em logs ou auditoria apresentada ao usuário.
    """
    digits = only_digits(value)
    if len(digits) == CPF_LENGTH:
        return f"{digits[:3]}.***.***-{digits[-2:]}"
    if len(digits) == CNPJ_LENGTH:
        return f"{digits[:2]}.***.***/****-{digits[-2:]}"
    if len(digits) <= 2:
        return "*" * len(digits)
    return f"{digits[:2]}{'*' * (len(digits) - 2)}"


@dataclass(frozen=True, slots=True)
class Document:
    """CPF ou CNPJ normalizado (somente dígitos) e classificado.

    Use :meth:`parse` para construir a partir de um valor bruto; o construtor
    direto assume que ``value`` já está normalizado e válido.
    """

    value: str
    type: DocumentType

    @classmethod
    def parse(cls, raw: str) -> Document:
        """Constrói a partir de um valor bruto, validando dígitos verificadores.

        Levanta :class:`InvalidDocumentError` quando o tamanho não corresponder a
        um CPF/CNPJ ou os dígitos verificadores forem inválidos.
        """
        digits = only_digits(raw)
        if len(digits) == CPF_LENGTH:
            if not is_valid_cpf(digits):
                raise InvalidDocumentError("CPF com dígitos verificadores inválidos")
            return cls(digits, DocumentType.CPF)
        if len(digits) == CNPJ_LENGTH:
            if not is_valid_cnpj(digits):
                raise InvalidDocumentError("CNPJ com dígitos verificadores inválidos")
            return cls(digits, DocumentType.CNPJ)
        raise InvalidDocumentError(
            "Documento deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)"
        )

    @property
    def masked(self) -> str:
        """Representação mascarada para exibição segura."""
        return mask_document(self.value)
