"""Testes da extração de padrões brasileiros em texto livre."""

from __future__ import annotations

from waypoint_etl.pipeline.cleaners.patterns import (
    find_cnpjs,
    find_cpfs,
    find_dates,
    find_documents,
    find_emails,
    find_labeled_value,
    find_money_values,
    find_phones,
    find_postal_codes,
)

# CPF e CNPJ sintéticos com dígitos verificadores corretos.
VALID_CPF = "390.533.447-05"
VALID_CPF_DIGITS = "39053344705"
VALID_CNPJ = "11.222.333/0001-81"
VALID_CNPJ_DIGITS = "11222333000181"

FICHA = f"""FICHA CADASTRAL DE CLIENTE - ERP LEGADO

Nome: Ana Maria Silva
CPF/CNPJ: {VALID_CPF}
E-mail: ANA.SILVA@Exemplo.com.br
Telefone: (11) 98765-4321
CEP: 01310-100
Data de Cadastro: 15/03/2024
Limite: R$ 1.234,56
"""


def test_find_cpfs_with_and_without_mask() -> None:
    text = f"CPF {VALID_CPF} e tambem {VALID_CPF_DIGITS}"

    assert find_cpfs(text) == [VALID_CPF_DIGITS]


def test_find_cpfs_rejects_invalid_check_digits() -> None:
    """Sem validar, qualquer sequência de 11 dígitos viraria CPF."""
    assert find_cpfs("Protocolo 111.111.111-11 e 12345678901") == []


def test_find_cnpjs() -> None:
    assert find_cnpjs(f"CNPJ: {VALID_CNPJ}") == [VALID_CNPJ_DIGITS]


def test_find_documents_returns_both_types() -> None:
    text = f"{VALID_CPF} / {VALID_CNPJ}"

    assert set(find_documents(text)) == {VALID_CPF_DIGITS, VALID_CNPJ_DIGITS}


def test_find_emails_normalizes_case_and_deduplicates() -> None:
    text = "ANA@Exemplo.com, ana@exemplo.com, bruno@exemplo.com.br"

    assert find_emails(text) == ["ana@exemplo.com", "bruno@exemplo.com.br"]


def test_find_phones() -> None:
    text = "Fones: (11) 98765-4321, +55 21 3456-7890"

    assert len(find_phones(text)) == 2


def test_find_postal_codes() -> None:
    assert find_postal_codes("CEP 01310-100 e 20040002") == ["01310-100", "20040002"]


def test_find_dates_keeps_raw_format() -> None:
    text = "Cadastro 15/03/2024, alterado em 2024-04-01"

    assert find_dates(text) == ["15/03/2024", "2024-04-01"]


def test_find_money_values() -> None:
    assert find_money_values("Total R$ 1.234,56 e R$ 99,90") == [
        "R$ 1.234,56",
        "R$ 99,90",
    ]


def test_patterns_do_not_match_inside_longer_numbers() -> None:
    """Bordas evitam recortar um pedaço de um número maior."""
    assert find_postal_codes("123456789012") == []
    assert find_cpfs("9" + VALID_CPF_DIGITS + "9") == []


def test_extract_fields_from_a_realistic_form() -> None:
    assert find_cpfs(FICHA) == [VALID_CPF_DIGITS]
    assert find_emails(FICHA) == ["ana.silva@exemplo.com.br"]
    assert find_postal_codes(FICHA) == ["01310-100"]
    assert find_dates(FICHA) == ["15/03/2024"]
    assert find_money_values(FICHA) == ["R$ 1.234,56"]


def test_find_labeled_value_supports_colon_and_pipe() -> None:
    assert find_labeled_value(FICHA, "Nome") == "Ana Maria Silva"
    assert find_labeled_value("CPF/CNPJ | 123", "CPF/CNPJ") == "123"


def test_find_labeled_value_is_case_insensitive_and_optional() -> None:
    assert find_labeled_value(FICHA, "nome") == "Ana Maria Silva"
    assert find_labeled_value(FICHA, "Inexistente") is None
