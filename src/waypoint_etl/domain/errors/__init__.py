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


class ExtractionError(WaypointError):
    """Falha controlada ao ler um arquivo de origem.

    Um arquivo inválido gera uma falha controlada; uma linha inválida, não
    (seção 17). Portanto este erro sinaliza problemas do arquivo como um todo.
    """


class UnsupportedFormatError(ExtractionError):
    """A extensão do arquivo não corresponde a nenhum formato suportado."""


class SourceNotFoundError(ExtractionError):
    """O arquivo de origem não existe ou não é um arquivo regular."""


class SheetNotFoundError(ExtractionError):
    """A aba informada no mapeamento não existe na planilha."""


class EmptySourceError(ExtractionError):
    """O arquivo não possui cabeçalho ou nenhuma linha de dados."""


__all__ = [
    "DomainError",
    "EmptySourceError",
    "ExtractionError",
    "InvalidDocumentError",
    "InvalidValueError",
    "SheetNotFoundError",
    "SourceNotFoundError",
    "UnsupportedFormatError",
    "WaypointError",
]
