"""Testes da geração de registros sintéticos de clientes."""

from __future__ import annotations

from pathlib import Path

from waypoint_etl.demo.synthetic import (
    CSV_HEADERS,
    generate_customer_rows,
    write_customers_csv,
)


def test_row_count_includes_duplicates() -> None:
    rows = generate_customer_rows(count=50)
    # 50 principais + 5 duplicatas anexadas.
    assert len(rows) == 55


def test_all_rows_have_expected_headers() -> None:
    rows = generate_customer_rows(count=50)
    for row in rows:
        assert set(row) == set(CSV_HEADERS)


def test_generation_is_deterministic() -> None:
    assert generate_customer_rows(seed=7) == generate_customer_rows(seed=7)


def test_contains_injected_invalid_documents() -> None:
    rows = generate_customer_rows(count=50)
    invalid = [r for r in rows if r["CPF_CNPJ"] == "111.111.111-11"]
    assert len(invalid) >= 1


def test_duplicates_share_document() -> None:
    rows = generate_customer_rows(count=50)
    dup_rows = [r for r in rows if r["Código"].endswith("-DUP")]
    assert len(dup_rows) == 5


def test_write_customers_csv(tmp_path: Path) -> None:
    target = write_customers_csv(tmp_path / "clientes.csv")
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "Nome Cliente" in content
    assert content.count("\n") >= 55
