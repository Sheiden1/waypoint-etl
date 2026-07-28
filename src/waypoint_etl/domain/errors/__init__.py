"""Hierarquia de erros do domínio.

Erros de um único registro nunca devem interromper o processamento do lote
(seção 13/17). Estes tipos são usados para sinalizar problemas de forma
controlada, sem vazar stack traces sensíveis ao usuário.
"""

from __future__ import annotations


class WaypointError(Exception):
    """Erro base para todo o Waypoint."""


class DomainError(WaypointError):
    """Erro originado na camada de domínio."""


class InvalidDocumentError(DomainError):
    """Documento (CPF/CNPJ) inválido: tamanho ou dígitos verificadores."""


class InvalidValueError(DomainError):
    """Valor inválido para um value object (e-mail, telefone, CEP, UF...)."""


__all__ = [
    "DomainError",
    "InvalidDocumentError",
    "InvalidValueError",
    "WaypointError",
]
