"""Value objects do domínio."""

from .brazilian_states import BRAZILIAN_UFS, is_valid_uf
from .document import (
    Document,
    is_valid_cnpj,
    is_valid_cpf,
    mask_document,
)

__all__ = [
    "BRAZILIAN_UFS",
    "Document",
    "is_valid_cnpj",
    "is_valid_cpf",
    "is_valid_uf",
    "mask_document",
]
