"""Configuração compartilhada de testes.

Testes devem ser determinísticos e nunca fazer chamadas de rede (seção 19).
"""

from __future__ import annotations

from random import Random

import pytest


@pytest.fixture
def rng() -> Random:
    """Gerador aleatório com semente fixa para testes determinísticos."""
    return Random(12345)
