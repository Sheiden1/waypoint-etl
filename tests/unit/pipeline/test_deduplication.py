"""Testes da detecção de duplicidades."""

from __future__ import annotations

from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.pipeline.deduplication import (
    annotate_duplicates,
    find_duplicates,
)
from waypoint_etl.pipeline.validators.result import ValidatedRecord

VALID_CPF = "39053344705"
OTHER_CPF = "12345678909"


def _record(row: int, **values: str | None) -> ValidatedRecord:
    """Registro válido (sem issues) para alimentar a deduplicação."""
    return ValidatedRecord(
        row_number=row,
        entity_type=EntityType.CUSTOMERS,
        values=values,
    )


def test_same_document_is_an_exact_duplicate() -> None:
    records = [
        _record(2, full_name="Ana Silva", document=VALID_CPF),
        _record(3, full_name="Ana S. Silva", document=VALID_CPF),
    ]

    result = find_duplicates(records)

    assert len(result.exact) == 1
    assert result.exact[0].row_number == 3
    assert result.exact[0].matched_row_number == 2
    assert result.exact[0].key == "document"
    assert result.duplicate_row_numbers == frozenset({3})


def test_same_email_is_an_exact_duplicate() -> None:
    records = [
        _record(2, full_name="Ana", document=VALID_CPF, email="ana@exemplo.com"),
        _record(3, full_name="Bruno", document=OTHER_CPF, email="ana@exemplo.com"),
    ]

    result = find_duplicates(records)

    assert len(result.exact) == 1
    assert result.exact[0].key == "email"


def test_same_external_id_is_an_exact_duplicate() -> None:
    records = [
        _record(2, full_name="Ana", external_id="ERP-1"),
        _record(3, full_name="Bruno", external_id="ERP-1"),
    ]

    result = find_duplicates(records)

    assert result.exact[0].key == "external_id"


def test_third_occurrence_points_to_the_first_row() -> None:
    records = [
        _record(2, full_name="Ana", document=VALID_CPF),
        _record(3, full_name="Ana", document=VALID_CPF),
        _record(4, full_name="Ana", document=VALID_CPF),
    ]

    result = find_duplicates(records)

    assert [match.matched_row_number for match in result.exact] == [2, 2]


def test_similar_name_and_same_phone_is_only_a_possibility() -> None:
    records = [
        _record(
            2, full_name="Ana Maria Silva", document=VALID_CPF, phone="11987654321"
        ),
        _record(3, full_name="Ana M. Silva", document=OTHER_CPF, phone="11987654321"),
    ]

    result = find_duplicates(records)

    assert result.exact == ()
    assert len(result.possible) == 1
    assert result.possible[0].key == "phone"
    assert result.possible[0].exact is False
    assert result.duplicate_row_numbers == frozenset()


def test_similar_name_and_same_postal_code_is_a_possibility() -> None:
    records = [
        _record(
            2, full_name="Ana Maria Silva", document=VALID_CPF, postal_code="01310100"
        ),
        _record(
            3, full_name="Ana Maria Silvo", document=OTHER_CPF, postal_code="01310100"
        ),
    ]

    result = find_duplicates(records)

    assert len(result.possible) == 1
    assert result.possible[0].key == "postal_code"


def test_similar_name_alone_is_not_enough() -> None:
    """Sem telefone ou CEP em comum, nomes parecidos não bastam."""
    records = [
        _record(2, full_name="Ana Maria Silva", document=VALID_CPF),
        _record(3, full_name="Ana Maria Silva", document=OTHER_CPF),
    ]

    result = find_duplicates(records)

    assert result.possible == ()


def test_different_names_with_same_phone_is_not_flagged() -> None:
    """Telefone de empresa compartilhado não faz de duas pessoas a mesma."""
    records = [
        _record(2, full_name="Ana Silva", document=VALID_CPF, phone="1133334444"),
        _record(
            3, full_name="Roberto Carvalho", document=OTHER_CPF, phone="1133334444"
        ),
    ]

    result = find_duplicates(records)

    assert result.possible == ()


def test_accents_and_case_do_not_hide_a_duplicate() -> None:
    records = [
        _record(2, full_name="JOSÉ ANTÔNIO", document=VALID_CPF, phone="11987654321"),
        _record(3, full_name="Jose Antonio", document=OTHER_CPF, phone="11987654321"),
    ]

    result = find_duplicates(records)

    assert len(result.possible) == 1


def test_rejected_records_are_not_compared() -> None:
    """Comparar registro já rejeitado só geraria ruído no relatório."""
    from waypoint_etl.domain.value_objects.issue import error

    records = [
        _record(2, full_name="Ana", document=VALID_CPF),
        ValidatedRecord(
            row_number=3,
            entity_type=EntityType.CUSTOMERS,
            values={"full_name": "Ana", "document": VALID_CPF},
            issues=(error("invalid_document", "x", field="document"),),
        ),
    ]

    result = find_duplicates(records)

    assert result.exact == ()


def test_no_duplicates_in_a_clean_batch() -> None:
    records = [
        _record(2, full_name="Ana", document=VALID_CPF),
        _record(3, full_name="Bruno", document=OTHER_CPF),
    ]

    result = find_duplicates(records)

    assert result.total == 0


def test_duplicates_never_reject_the_record() -> None:
    """Seção 14: nunca mesclar nem descartar automaticamente."""
    records = [
        _record(2, full_name="Ana", document=VALID_CPF),
        _record(3, full_name="Ana", document=VALID_CPF),
    ]
    result = find_duplicates(records)

    annotated = annotate_duplicates(records, result)

    assert all(record.is_valid for record in annotated)
    assert annotated[1].warnings
    assert annotated[1].warnings[0].code == "duplicate_exact"


def test_annotation_keeps_records_without_matches_untouched() -> None:
    records = [_record(2, full_name="Ana", document=VALID_CPF)]

    annotated = annotate_duplicates(records, find_duplicates(records))

    assert annotated[0] is records[0]
