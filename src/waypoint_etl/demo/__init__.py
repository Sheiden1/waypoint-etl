"""Geração de dados sintéticos de demonstração.

Todos os documentos (CPF/CNPJ) são gerados programaticamente com dígitos
verificadores válidos, mas **não** correspondem a pessoas reais (seção 22 do
CLAUDE.md). Nunca utilize dados pessoais reais no repositório.
"""

from .documents import generate_cnpj, generate_cpf
from .synthetic import generate_customer_rows, write_customers_csv

__all__ = [
    "generate_cnpj",
    "generate_cpf",
    "generate_customer_rows",
    "write_customers_csv",
]
