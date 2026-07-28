"""Integração com PostgreSQL real.

Só roda quando ``WAYPOINT_TEST_DATABASE_URL`` aponta para um banco de teste
descartável, por exemplo::

    docker compose up -d db
    export WAYPOINT_TEST_DATABASE_URL=postgresql+psycopg://waypoint:waypoint@localhost:5432/waypoint_test
    uv run pytest tests/integration/test_postgres_load.py

Sem a variável, os testes são pulados: a suíte não pode depender de um serviço
externo (seção 19), mas o caminho real precisa existir para a seção 26.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import Engine, create_engine, func, select

from waypoint_etl.application.dto.migration import MigrationRun
from waypoint_etl.domain.entities.customer import Customer
from waypoint_etl.domain.enums.document_type import DocumentType
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.enums.run_status import RunStatus
from waypoint_etl.infrastructure.database.models import Base, CustomerModel
from waypoint_etl.infrastructure.database.session import check_connection, session_scope
from waypoint_etl.infrastructure.loaders.postgres_loader import (
    DryRunWriteAttemptError,
    load_records,
)
from waypoint_etl.pipeline.validators.result import ValidatedRecord

TEST_DATABASE_URL = os.environ.get("WAYPOINT_TEST_DATABASE_URL")
VALID_CPF = "39053344705"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="defina WAYPOINT_TEST_DATABASE_URL para rodar contra PostgreSQL",
    ),
]


@pytest.fixture
def engine() -> Engine:
    """Engine para o banco de teste, com o schema recriado do zero."""
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, future=True)
    if not check_connection(engine):
        pytest.skip(f"não foi possível conectar em {TEST_DATABASE_URL}")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


def _record(row: int) -> ValidatedRecord:
    return ValidatedRecord(
        row_number=row,
        entity_type=EntityType.CUSTOMERS,
        values={"full_name": "Ana Silva", "document": VALID_CPF},
        entity=Customer(
            full_name="Ana Silva",
            document=VALID_CPF,
            document_type=DocumentType.CPF,
            external_id=f"ERP-{row}",
        ),
    )


def _run(*, dry_run: bool) -> MigrationRun:
    return MigrationRun(
        entity=EntityType.CUSTOMERS,
        source_filename="clientes.xlsx",
        source_hash="a" * 64,
        dry_run=dry_run,
    )


def test_load_into_postgres(engine: Engine) -> None:
    result = load_records(engine, [_record(2), _record(3)], _run(dry_run=False))

    with session_scope(engine) as session:
        total = session.scalar(select(func.count()).select_from(CustomerModel))

    assert result.loaded_records == 2
    assert total == 2
    assert result.run.status is RunStatus.COMPLETED


def test_dry_run_does_not_write_to_postgres(engine: Engine) -> None:
    with pytest.raises(DryRunWriteAttemptError):
        load_records(engine, [_record(2)], _run(dry_run=True))

    with session_scope(engine) as session:
        total = session.scalar(select(func.count()).select_from(CustomerModel))

    assert total == 0
