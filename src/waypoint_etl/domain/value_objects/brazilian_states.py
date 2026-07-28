"""Unidades federativas (UF) oficiais do Brasil."""

from __future__ import annotations

BRAZILIAN_UFS: frozenset[str] = frozenset(
    {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
        "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    }
)


def is_valid_uf(value: str | None) -> bool:
    """Indica se ``value`` é uma sigla de UF válida (ignora caixa e espaços)."""
    if not value:
        return False
    return value.strip().upper() in BRAZILIAN_UFS
