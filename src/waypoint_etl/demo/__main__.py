"""Ponto de entrada para geração dos dados de demonstração.

Uso::

    python -m waypoint_etl.demo            # escreve em samples/input/
    python -m waypoint_etl.demo ./out      # escreve em ./out

Alvo do Makefile: ``make demo-data``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .synthetic import write_customers_csv, write_legacy_xlsx


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    base = Path(args[0]) if args else Path("samples/input")
    targets = [
        write_customers_csv(base / "clientes_legado.csv"),
        write_legacy_xlsx(base / "clientes_legado.xlsx"),
    ]
    # Saída de script utilitário (fora do núcleo da aplicação).
    for target in targets:
        print(f"Dados de demonstração gerados em: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
