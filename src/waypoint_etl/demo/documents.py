"""Geração de CPFs e CNPJs sintéticos com dígitos verificadores válidos.

Estes documentos são fabricados apenas para teste/demonstração. Os dígitos
verificadores são calculados corretamente para que passem na validação, mas os
números não pertencem a pessoas ou empresas reais.
"""

from __future__ import annotations

from random import Random


def _cpf_check_digits(base: list[int]) -> tuple[int, int]:
    """Calcula os dois dígitos verificadores de um CPF a partir dos 9 primeiros."""
    def digit(nums: list[int]) -> int:
        weight = len(nums) + 1
        total = sum(n * (weight - i) for i, n in enumerate(nums))
        check = (total * 10) % 11
        return 0 if check == 10 else check

    d1 = digit(base)
    d2 = digit([*base, d1])
    return d1, d2


def _cnpj_check_digits(base: list[int]) -> tuple[int, int]:
    """Calcula os dois dígitos verificadores de um CNPJ a partir dos 12 primeiros."""
    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_second = [6, *weights_first]

    def digit(nums: list[int], weights: list[int]) -> int:
        total = sum(n * w for n, w in zip(nums, weights, strict=True))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    d1 = digit(base, weights_first)
    d2 = digit([*base, d1], weights_second)
    return d1, d2


def generate_cpf(rng: Random | None = None) -> str:
    """Gera um CPF sintético válido (11 dígitos, somente números)."""
    rng = rng or Random()
    base = [rng.randint(0, 9) for _ in range(9)]
    # Evita sequências repetidas (que são rejeitadas pela validação).
    if len(set(base)) == 1:
        base[0] = (base[0] + 1) % 10
    d1, d2 = _cpf_check_digits(base)
    return "".join(map(str, [*base, d1, d2]))


def generate_cnpj(rng: Random | None = None) -> str:
    """Gera um CNPJ sintético válido (14 dígitos, somente números)."""
    rng = rng or Random()
    base = [rng.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    d1, d2 = _cnpj_check_digits(base)
    return "".join(map(str, [*base, d1, d2]))
