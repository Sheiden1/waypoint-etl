"""Detecção de duplicidades entre registros validados (seção 14).

Duas estratégias, com pesos diferentes:

* **correspondência exata** — mesmo CPF/CNPJ, mesmo identificador externo ou
  mesmo e-mail normalizado. Marca o registro como duplicado.
* **possível duplicidade** — nome semelhante com mesmo telefone ou mesmo CEP.
  Apenas alerta.

O MVP nunca mescla dois registros automaticamente: a decisão é de quem conduz a
migração, e uma mesclagem errada é irreversível.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ...domain.value_objects.issue import Issue, warning
from ..normalizers.text import remove_accents
from ..validators.result import ValidatedRecord

# Acima deste ponto de corte dois nomes são considerados semelhantes. Calibrado
# para reconhecer abreviações do nome do meio ("Ana Maria Silva" x "Ana M.
# Silva", ~0.81) e erros de digitação. Um limiar mais alto perderia esse caso,
# que é a duplicata mais comum em cadastro legado.
#
# O viés é deliberado: como a suspeita só gera alerta e nunca mescla registros,
# um falso positivo custa uma revisão, enquanto um falso negativo deixa uma
# duplicata entrar no sistema de destino. Além da semelhança de nome, ainda é
# exigido telefone ou CEP idêntico, o que contém os falsos positivos.
NAME_SIMILARITY_THRESHOLD = 0.80

# Chaves de correspondência exata, na ordem de confiança.
EXACT_KEYS: tuple[str, ...] = ("document", "customer_document", "external_id", "email")


@dataclass(frozen=True, slots=True)
class DuplicateMatch:
    """Uma correspondência entre o registro atual e um anterior."""

    row_number: int
    matched_row_number: int
    key: str
    value: str
    exact: bool
    similarity: float = 1.0


@dataclass(frozen=True, slots=True)
class DeduplicationResult:
    """Resultado da análise de duplicidades de um lote."""

    exact: tuple[DuplicateMatch, ...] = field(default_factory=tuple)
    possible: tuple[DuplicateMatch, ...] = field(default_factory=tuple)

    @property
    def duplicate_row_numbers(self) -> frozenset[int]:
        """Linhas marcadas como duplicata exata."""
        return frozenset(match.row_number for match in self.exact)

    @property
    def total(self) -> int:
        """Quantidade total de correspondências encontradas."""
        return len(self.exact) + len(self.possible)

    def issues_for(self, row_number: int) -> tuple[Issue, ...]:
        """Alertas de duplicidade associados a uma linha.

        Duplicidade nunca gera ``error``: o registro continua importável e a
        decisão fica com o usuário.
        """
        issues: list[Issue] = []
        for match in self.exact:
            if match.row_number == row_number:
                issues.append(
                    warning(
                        "duplicate_exact",
                        f"Registro duplicado: mesmo '{match.key}' da linha "
                        f"{match.matched_row_number}.",
                        field=match.key,
                        original_value=match.value,
                    )
                )
        for match in self.possible:
            if match.row_number == row_number:
                issues.append(
                    warning(
                        "duplicate_possible",
                        f"Possível duplicata da linha {match.matched_row_number} "
                        f"(nome semelhante e mesmo '{match.key}'). Revise antes "
                        "de importar.",
                        field=match.key,
                        original_value=match.value,
                    )
                )
        return tuple(issues)


def find_duplicates(
    records: Sequence[ValidatedRecord],
    *,
    threshold: float = NAME_SIMILARITY_THRESHOLD,
) -> DeduplicationResult:
    """Analisa um lote e devolve as correspondências encontradas.

    Só registros válidos entram na comparação: um registro rejeitado já não vai
    ser importado, e compará-lo geraria ruído no relatório.
    """
    candidates = [record for record in records if record.is_valid]

    exact = _find_exact(candidates)
    possible = _find_possible(candidates, threshold, exact)
    return DeduplicationResult(exact=tuple(exact), possible=tuple(possible))


def _find_exact(records: Sequence[ValidatedRecord]) -> list[DuplicateMatch]:
    """Correspondência exata por documento, identificador externo ou e-mail."""
    matches: list[DuplicateMatch] = []
    seen: dict[tuple[str, str], int] = {}

    for record in records:
        keys = [
            (key, value)
            for key in EXACT_KEYS
            if (value := _normalized(record, key)) is not None
        ]

        # A primeira chave que já apareceu basta para marcar a linha.
        for key, value in keys:
            previous = seen.get((key, value))
            if previous is not None:
                matches.append(
                    DuplicateMatch(
                        row_number=record.row_number,
                        matched_row_number=previous,
                        key=key,
                        value=value,
                        exact=True,
                    )
                )
                break

        # Todas as chaves são registradas, inclusive as de uma duplicata, para
        # que a próxima ocorrência aponte sempre para a primeira linha vista.
        for key, value in keys:
            seen.setdefault((key, value), record.row_number)

    return matches


def _find_possible(
    records: Sequence[ValidatedRecord],
    threshold: float,
    exact: Sequence[DuplicateMatch],
) -> list[DuplicateMatch]:
    """Nome semelhante com mesmo telefone ou mesmo CEP."""
    already_exact = {match.row_number for match in exact}
    matches: list[DuplicateMatch] = []

    for index, record in enumerate(records):
        if record.row_number in already_exact:
            continue
        name = _comparable_name(record)
        if name is None:
            continue

        for previous in records[:index]:
            previous_name = _comparable_name(previous)
            if previous_name is None:
                continue

            similarity = _similarity(name, previous_name)
            if similarity < threshold:
                continue

            key = _shared_secondary_key(record, previous)
            if key is None:
                continue

            matches.append(
                DuplicateMatch(
                    row_number=record.row_number,
                    matched_row_number=previous.row_number,
                    key=key,
                    value=_normalized(record, key) or "",
                    exact=False,
                    similarity=round(similarity, 3),
                )
            )
            break

    return matches


def _shared_secondary_key(
    record: ValidatedRecord, other: ValidatedRecord
) -> str | None:
    """Telefone ou CEP em comum entre dois registros."""
    for key in ("phone", "postal_code"):
        value = _normalized(record, key)
        if value is not None and value == _normalized(other, key):
            return key
    return None


def _normalized(record: ValidatedRecord, key: str) -> str | None:
    """Valor de um campo pronto para comparação (minúsculo, sem espaços)."""
    value = record.values.get(key)
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _comparable_name(record: ValidatedRecord) -> str | None:
    """Nome sem acentos e em minúsculas, para comparação aproximada."""
    raw = record.values.get("full_name") or record.values.get("name")
    if raw is None:
        return None
    simplified = remove_accents(raw.strip().lower())
    return simplified or None


def _similarity(left: str, right: str) -> float:
    """Similaridade entre dois nomes, de 0 a 1."""
    return SequenceMatcher(None, left, right).ratio()


def annotate_duplicates(
    records: Iterable[ValidatedRecord], result: DeduplicationResult
) -> tuple[ValidatedRecord, ...]:
    """Devolve os registros com os alertas de duplicidade incorporados."""
    annotated: list[ValidatedRecord] = []
    for record in records:
        issues = result.issues_for(record.row_number)
        if not issues:
            annotated.append(record)
            continue
        annotated.append(
            ValidatedRecord(
                row_number=record.row_number,
                entity_type=record.entity_type,
                values=record.values,
                issues=record.issues + issues,
                entity=record.entity,
                sheet=record.sheet,
            )
        )
    return tuple(annotated)


__all__ = [
    "EXACT_KEYS",
    "NAME_SIMILARITY_THRESHOLD",
    "DeduplicationResult",
    "DuplicateMatch",
    "annotate_duplicates",
    "find_duplicates",
]
