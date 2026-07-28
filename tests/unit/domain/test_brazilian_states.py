"""Testes da validação de UF."""

from __future__ import annotations

import pytest

from waypoint_etl.domain.value_objects import BRAZILIAN_UFS, is_valid_uf


def test_has_27_ufs() -> None:
    assert len(BRAZILIAN_UFS) == 27


@pytest.mark.parametrize("value", ["SP", "sp", " rj ", "DF"])
def test_valid_uf(value: str) -> None:
    assert is_valid_uf(value) is True


@pytest.mark.parametrize("value", ["XX", "", None, "São Paulo"])
def test_invalid_uf(value: str | None) -> None:
    assert is_valid_uf(value) is False
