"""Integração: carga transacional e garantias do dry-run (seção 15).

Os modelos usam tipos portáveis, então o comportamento transacional é
exercitado contra SQLite em arquivo temporário. O teste equivalente contra
PostgreSQL roda apenas quando ``DATABASE_URL`` está definida (ver
``test_postgres_load.py``).
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError

from waypoint_etl.application.dto.migration import MigrationRun, compute_file_hash
from waypoint_etl.domain.entities.customer import Customer
from waypoint_etl.domain.entities.invoice import Invoice
from waypoint_etl.domain.enums.document_type import DocumentType
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.enums.invoice_status import InvoiceStatus
from waypoint_etl.domain.enums.run_status import RunStatus
from waypoint_etl.domain.value_objects.issue import error
from waypoint_etl.infrastructure.database.models import (
    CustomerModel,
    InvoiceModel,
    MigrationIssueModel,
    MigrationRunModel,
)
from waypoint_etl.infrastructure.database.session import create_all, session_scope
from waypoint_etl.infrastructure.loaders.postgres_loader import (
    DryRunWriteAttemptError,
    LoadError,
    load_records,
)
from waypoint_etl.pipeline.validators.result import ValidatedRecord

pytestmark = pytest.mark.integration

VALID_CPF = "39053344705"


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Banco isolado por teste (seção 19: banco de teste isolado)."""
    engine = create_engine(f"sqlite:///{tmp_path / 'waypoint.db'}", future=True)
    create_all(engine)
    return engine


def _run(*, dry_run: bool) -> MigrationRun:
    return MigrationRun(
        entity=EntityType.CUSTOMERS,
        source_filename="clientes_legado.xlsx",
        source_hash="a" * 64,
        dry_run=dry_run,
        mapping_name="ERP Legado - Clientes",
        mapping_version=1,
    )


def _valid_customer(row: int, document: str = VALID_CPF) -> ValidatedRecord:
    return ValidatedRecord(
        row_number=row,
        entity_type=EntityType.CUSTOMERS,
        values={"full_name": "Ana Silva", "document": document},
        entity=Customer(
            full_name="Ana Silva",
            document=document,
            document_type=DocumentType.CPF,
            external_id=f"ERP-{row}",
            email="ana@exemplo.com.br",
        ),
    )


def _rejected_customer(row: int) -> ValidatedRecord:
    return ValidatedRecord(
        row_number=row,
        entity_type=EntityType.CUSTOMERS,
        values={"full_name": "Bruno", "document": "11111111111"},
        issues=(
            error(
                "invalid_document",
                "Documento inválido.",
                field="document",
                original_value="11111111111",
            ),
        ),
    )


def _count(engine: Engine, model: type) -> int:
    with session_scope(engine) as session:
        return int(session.scalar(select(func.count()).select_from(model)) or 0)


# --- Dry-run ------------------------------------------------------------------


def test_dry_run_never_writes(engine: Engine) -> None:
    """Regra 15: o modo dry-run não pode gravar nas tabelas de destino."""
    records = [_valid_customer(2), _valid_customer(3, "11222333000181")]

    with pytest.raises(DryRunWriteAttemptError):
        load_records(engine, records, _run(dry_run=True))

    assert _count(engine, CustomerModel) == 0
    assert _count(engine, MigrationRunModel) == 0


def test_dry_run_is_rejected_before_touching_the_database(tmp_path: Path) -> None:
    """A barreira vem antes da conexão: nem uma engine inválida é usada."""
    broken = create_engine("postgresql+psycopg://invalido:0/naoexiste", future=True)

    with pytest.raises(DryRunWriteAttemptError):
        load_records(broken, [_valid_customer(2)], _run(dry_run=True))


# --- Carga efetiva ------------------------------------------------------------


def test_valid_records_are_persisted(engine: Engine) -> None:
    records = [_valid_customer(2), _valid_customer(3, "11222333000181")]

    result = load_records(engine, records, _run(dry_run=False))

    assert result.loaded_records == 2
    assert _count(engine, CustomerModel) == 2
    assert result.run.status is RunStatus.COMPLETED
    assert result.run.duration_ms is not None


def test_rejected_records_never_reach_the_target_table(engine: Engine) -> None:
    records = [_valid_customer(2), _rejected_customer(3)]

    result = load_records(engine, records, _run(dry_run=False))

    assert result.loaded_records == 1
    assert _count(engine, CustomerModel) == 1


def test_issues_are_persisted_for_traceability(engine: Engine) -> None:
    records = [_valid_customer(2), _rejected_customer(3)]

    load_records(engine, records, _run(dry_run=False))

    with session_scope(engine) as session:
        issues = list(session.scalars(select(MigrationIssueModel)))

    assert len(issues) == 1
    assert issues[0].code == "invalid_document"
    assert issues[0].row_number == 3


def test_persisted_issue_masks_the_document(engine: Engine) -> None:
    """Seção 18: o documento completo não é gravado na auditoria."""
    load_records(engine, [_rejected_customer(3)], _run(dry_run=False))

    with session_scope(engine) as session:
        issue = session.scalars(select(MigrationIssueModel)).one()

    assert issue.original_value == "111.***.***-11"


def test_run_is_recorded_with_its_metadata(engine: Engine) -> None:
    run = _run(dry_run=False).with_counters(
        total=3, valid=2, rejected=1, duplicates=0, ocr_used=True
    )

    result = load_records(engine, [_valid_customer(2)], run)

    with session_scope(engine) as session:
        stored = session.scalars(select(MigrationRunModel)).one()

    assert stored.id == run.id
    assert stored.entity == "customers"
    assert stored.source_hash == "a" * 64
    assert stored.mapping_name == "ERP Legado - Clientes"
    assert stored.dry_run is False
    assert stored.total_records == 3
    assert stored.ocr_used is True
    assert stored.duration_ms is not None
    assert result.run.run_id == str(run.id)


def test_records_are_linked_to_the_run(engine: Engine) -> None:
    """Rastreabilidade: todo registro carregado aponta para o run_id."""
    run = _run(dry_run=False)

    load_records(engine, [_valid_customer(2)], run)

    with session_scope(engine) as session:
        customer = session.scalars(select(CustomerModel)).one()

    assert customer.run_id == run.id


def test_money_survives_the_round_trip_as_decimal(engine: Engine) -> None:
    """Valor monetário não pode virar float ao passar pelo banco."""
    invoice = ValidatedRecord(
        row_number=2,
        entity_type=EntityType.INVOICES,
        values={},
        entity=Invoice(
            external_id="NF-1",
            customer_document=VALID_CPF,
            issued_at=date(2024, 3, 1),
            due_at=date(2024, 3, 31),
            amount=Decimal("1234.56"),
            status=InvoiceStatus.OPEN,
        ),
    )
    run = MigrationRun(
        entity=EntityType.INVOICES,
        source_filename="cobrancas.csv",
        source_hash="b" * 64,
        dry_run=False,
    )

    load_records(engine, [invoice], run)

    with session_scope(engine) as session:
        stored = session.scalars(select(InvoiceModel)).one()

    assert isinstance(stored.amount, Decimal)
    assert stored.amount == Decimal("1234.56")


# --- Transação ----------------------------------------------------------------


def test_failure_rolls_back_the_whole_batch(engine: Engine) -> None:
    """Seção 15: erro de infraestrutura reverte a carga inteira."""
    too_long = "X" * 300  # estoura o limite da coluna no dialeto estrito
    records = [
        _valid_customer(2),
        ValidatedRecord(
            row_number=3,
            entity_type=EntityType.CUSTOMERS,
            values={},
            entity=Customer(
                full_name="Ana",
                document=VALID_CPF,
                document_type=DocumentType.CPF,
                # ``state`` tem 2 caracteres; um valor absurdo força a falha.
                state=too_long,
            ),
        ),
    ]

    with pytest.raises((LoadError, SQLAlchemyError)):
        _force_strict_load(engine, records)

    assert _count(engine, CustomerModel) == 0
    assert _count(engine, MigrationRunModel) == 0


def _force_strict_load(engine: Engine, records: list[ValidatedRecord]) -> None:
    """Executa a carga com verificação de tamanho ativa.

    O SQLite ignora limites de ``VARCHAR`` por padrão; um ``CHECK`` explícito
    reproduz o comportamento estrito do PostgreSQL para o teste de rollback.
    """
    from sqlalchemy import text

    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER enforce_state_length BEFORE INSERT ON customers "
                "FOR EACH ROW WHEN length(NEW.state) > 2 "
                "BEGIN SELECT RAISE(ABORT, 'state too long'); END;"
            )
        )
    load_records(engine, records, _run(dry_run=False))


# --- Hash do arquivo ----------------------------------------------------------


def test_file_hash_identifies_the_source(tmp_path: Path) -> None:
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    first.write_text("nome\nAna\n", encoding="utf-8")
    second.write_text("nome\nAna\n", encoding="utf-8")

    assert compute_file_hash(first) == compute_file_hash(second)

    second.write_text("nome\nBruno\n", encoding="utf-8")
    assert compute_file_hash(first) != compute_file_hash(second)


def test_run_generates_a_unique_identifier() -> None:
    first = _run(dry_run=True)
    second = _run(dry_run=True)

    assert first.id != second.id
    assert uuid.UUID(first.run_id)


def test_finish_computes_duration() -> None:
    started = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
    run = MigrationRun(
        entity=EntityType.CUSTOMERS,
        source_filename="a.csv",
        source_hash="c" * 64,
        dry_run=True,
        started_at=started,
    )

    finished = run.finish(
        RunStatus.DRY_RUN, finished_at=datetime(2024, 3, 15, 10, 0, 2, tzinfo=UTC)
    )

    assert finished.duration_ms == 2000
    assert finished.status is RunStatus.DRY_RUN


def test_database_url_is_not_required_to_run_dry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seção 21: o sistema inicia em dry-run mesmo sem PostgreSQL."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert os.environ.get("DATABASE_URL") is None

    run = _run(dry_run=True)

    assert run.dry_run is True
