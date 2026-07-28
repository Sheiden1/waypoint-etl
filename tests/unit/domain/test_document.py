"""Testes do value object Document e da validação de CPF/CNPJ."""

from __future__ import annotations

import pytest

from waypoint_etl.domain.enums import DocumentType
from waypoint_etl.domain.errors import InvalidDocumentError
from waypoint_etl.domain.value_objects import (
    Document,
    is_valid_cnpj,
    is_valid_cpf,
    mask_document,
)

# Vetores conhecidos e sintéticos (não pertencem a pessoas reais).
VALID_CPF = "111.444.777-35"
VALID_CPF_DIGITS = "11144477735"
VALID_CNPJ = "11.222.333/0001-81"
VALID_CNPJ_DIGITS = "11222333000181"


class TestCpf:
    def test_valid_cpf_with_mask(self) -> None:
        assert is_valid_cpf(VALID_CPF) is True

    def test_valid_cpf_without_mask(self) -> None:
        assert is_valid_cpf(VALID_CPF_DIGITS) is True

    @pytest.mark.parametrize(
        "value",
        [
            "111.444.777-30",  # dígito verificador errado
            "00000000000",  # todos iguais
            "111",  # curto demais
            "1114447773",  # 10 dígitos
            "",
            "abcdefghijk",
        ],
    )
    def test_invalid_cpf(self, value: str) -> None:
        assert is_valid_cpf(value) is False


class TestCnpj:
    def test_valid_cnpj_with_mask(self) -> None:
        assert is_valid_cnpj(VALID_CNPJ) is True

    def test_valid_cnpj_without_mask(self) -> None:
        assert is_valid_cnpj(VALID_CNPJ_DIGITS) is True

    @pytest.mark.parametrize(
        "value",
        [
            "11.222.333/0001-80",  # dígito verificador errado
            "00000000000000",  # todos iguais
            "12345",  # curto demais
            "",
        ],
    )
    def test_invalid_cnpj(self, value: str) -> None:
        assert is_valid_cnpj(value) is False


class TestDocumentParse:
    def test_parse_cpf(self) -> None:
        doc = Document.parse(VALID_CPF)
        assert doc.value == VALID_CPF_DIGITS
        assert doc.type is DocumentType.CPF

    def test_parse_cnpj(self) -> None:
        doc = Document.parse(VALID_CNPJ)
        assert doc.value == VALID_CNPJ_DIGITS
        assert doc.type is DocumentType.CNPJ

    def test_parse_invalid_check_digit_raises(self) -> None:
        with pytest.raises(InvalidDocumentError):
            Document.parse("111.444.777-30")

    def test_parse_wrong_length_raises(self) -> None:
        with pytest.raises(InvalidDocumentError):
            Document.parse("123")

    def test_document_is_frozen(self) -> None:
        doc = Document.parse(VALID_CPF)
        with pytest.raises(AttributeError):
            doc.value = "outro"  # type: ignore[misc]


class TestMask:
    def test_mask_cpf_hides_middle_digits(self) -> None:
        masked = mask_document(VALID_CPF_DIGITS)
        assert masked == "111.***.***-35"
        assert VALID_CPF_DIGITS not in masked

    def test_mask_cnpj_hides_middle_digits(self) -> None:
        masked = mask_document(VALID_CNPJ_DIGITS)
        assert "***" in masked
        assert VALID_CNPJ_DIGITS not in masked

    def test_document_masked_property(self) -> None:
        doc = Document.parse(VALID_CPF)
        assert doc.masked == "111.***.***-35"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("12", "**"),  # <= 2 dígitos: mascara tudo
            ("123456", "12****"),  # tamanho atípico: preserva 2, mascara o resto
        ],
    )
    def test_mask_atypical_length(self, value: str, expected: str) -> None:
        assert mask_document(value) == expected
