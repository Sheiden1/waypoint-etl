"""Ponto de entrada para geração dos dados de demonstração.

Uso::

    python -m waypoint_etl.demo            # escreve em samples/input/
    python -m waypoint_etl.demo ./out      # escreve em ./out

Alvo do Makefile: ``make demo-data``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .document_files import (
    write_customer_form_docx,
    write_customer_form_pdf,
    write_customers_txt,
    write_scanned_form_image,
    write_scanned_form_pdf,
)
from .synthetic import write_customers_csv, write_legacy_xlsx


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    base = Path(args[0]) if args else Path("samples/input")
    targets = [
        write_customers_csv(base / "clientes_legado.csv"),
        write_legacy_xlsx(base / "clientes_legado.xlsx"),
        write_customers_txt(base / "clientes_legado.txt"),
        write_customer_form_docx(base / "ficha_cadastral.docx"),
        write_customer_form_pdf(base / "ficha_cadastral.pdf"),
        write_scanned_form_pdf(base / "ficha_escaneada.pdf"),
        write_scanned_form_image(base / "ficha_escaneada.png"),
    ]
    # Saída de script utilitário (fora do núcleo da aplicação).
    for target in targets:
        print(f"Dados de demonstração gerados em: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
