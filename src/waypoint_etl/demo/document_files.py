"""Documentos sintéticos de demonstração (TXT, DOCX e PDF digital).

Reproduzem o formato de fichas cadastrais e relatórios exportados por sistemas
antigos: rótulo e valor na mesma linha, para exercitar a extração por Regex.

Os dados vêm do mesmo gerador determinístico dos arquivos tabulares, portanto
são inteiramente sintéticos (seção 22).
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from docx import Document

from .synthetic import FIXTURE_TIMESTAMP, generate_customer_rows

# Campos exibidos na ficha, na ordem em que aparecem no documento.
FORM_FIELDS = (
    ("Código", "Código"),
    ("Nome", "Nome Cliente"),
    ("CPF/CNPJ", "CPF_CNPJ"),
    ("E-mail", "Correio Eletrônico"),
    ("Telefone", "Fone Principal"),
    ("CEP", "CEP"),
    ("Cidade", "Cidade"),
    ("UF", "UF"),
    ("Data de Cadastro", "Data Cadastro"),
)

FORM_TITLE = "FICHA CADASTRAL DE CLIENTE - ERP LEGADO"
TXT_TITLE = "RELATORIO DE CLIENTES - ERP LEGADO"
TXT_SEPARATOR = "-" * 62

_DEFAULT_FORM_COUNT = 3


def _form_lines(row: dict[str, str]) -> list[str]:
    """Monta as linhas ``Rótulo: valor`` de uma ficha."""
    return [f"{label}: {row[column]}".rstrip() for label, column in FORM_FIELDS]


def write_customers_txt(
    path: Path, *, seed: int = 20240101, count: int = 10
) -> Path:
    """Escreve um relatório de clientes em texto puro."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_customer_rows(seed=seed, count=count)[:count]

    lines = [TXT_TITLE, TXT_SEPARATOR]
    for row in rows:
        lines.extend(_form_lines(row))
        lines.append(TXT_SEPARATOR)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_customer_form_docx(
    path: Path, *, seed: int = 20240101, count: int = _DEFAULT_FORM_COUNT
) -> Path:
    """Escreve fichas cadastrais em Word, misturando parágrafos e tabela."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_customer_rows(seed=seed, count=count)[:count]

    document = Document()
    document.add_heading(FORM_TITLE, level=1)

    for row in rows:
        document.add_paragraph(f"Cliente {row['Código']}")
        # Uma tabela rótulo/valor, como nas fichas digitalizadas de verdade.
        table = document.add_table(rows=0, cols=2)
        for label, column in FORM_FIELDS:
            cells = table.add_row().cells
            cells[0].text = label
            cells[1].text = row[column]
        document.add_paragraph("")

    document.core_properties.created = FIXTURE_TIMESTAMP
    document.core_properties.modified = FIXTURE_TIMESTAMP
    document.save(str(path))
    return path


def write_customer_form_pdf(
    path: Path, *, seed: int = 20240101, count: int = _DEFAULT_FORM_COUNT
) -> Path:
    """Escreve fichas cadastrais em PDF com camada de texto (uma por página)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_customer_rows(seed=seed, count=count)[:count]

    document = pymupdf.open()
    try:
        for row in rows:
            page = document.new_page()
            body = "\n".join([FORM_TITLE, "", *_form_lines(row)])
            # Margem de 72pt (uma polegada) em relação ao tamanho A4 padrão.
            box = pymupdf.Rect(72, 72, page.rect.width - 72, page.rect.height - 72)
            page.insert_textbox(box, body, fontsize=11, fontname="helv")
        stamp = FIXTURE_TIMESTAMP.strftime("D:%Y%m%d%H%M%SZ")
        document.set_metadata({"creationDate": stamp, "modDate": stamp})
        document.save(path)
    finally:
        document.close()
    return path


__all__ = [
    "FORM_FIELDS",
    "FORM_TITLE",
    "TXT_TITLE",
    "write_customer_form_docx",
    "write_customer_form_pdf",
    "write_customers_txt",
]
