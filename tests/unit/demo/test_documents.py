"""Testes dos geradores de documentos sintéticos."""

from __future__ import annotations

from random import Random

from waypoint_etl.demo import generate_cnpj, generate_cpf
from waypoint_etl.domain.value_objects import is_valid_cnpj, is_valid_cpf


def test_generated_cpfs_are_valid() -> None:
    rng = Random(1)
    for _ in range(200):
        assert is_valid_cpf(generate_cpf(rng))


def test_generated_cnpjs_are_valid() -> None:
    rng = Random(2)
    for _ in range(200):
        assert is_valid_cnpj(generate_cnpj(rng))


def test_generation_is_deterministic() -> None:
    assert generate_cpf(Random(42)) == generate_cpf(Random(42))
    assert generate_cnpj(Random(42)) == generate_cnpj(Random(42))
