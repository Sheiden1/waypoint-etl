"""Modelos SQLAlchemy das tabelas de destino e de auditoria (seção 15).

Os tipos são escolhidos para funcionar tanto no PostgreSQL quanto no SQLite: o
``Uuid`` do SQLAlchemy vira ``UUID`` nativo no Postgres e ``CHAR(32)`` no
SQLite, o que permite testar o comportamento transacional sem subir um banco.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Precisão suficiente para valores monetários de cobrança, sem usar float.
MONEY_PRECISION = 18
MONEY_SCALE = 2


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos."""


def _now() -> datetime:
    """Horário atual em UTC, usado como padrão das colunas de criação."""
    return datetime.now(UTC)


class MigrationRunModel(Base):
    """Uma execução de migração, identificada pelo ``run_id`` (seção 15)."""

    __tablename__ = "migration_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    entity: Mapped[str] = mapped_column(String(20), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mapping_name: Mapped[str | None] = mapped_column(String(120))
    mapping_version: Mapped[int | None] = mapped_column(Integer)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    issues: Mapped[list[MigrationIssueModel]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class MigrationIssueModel(Base):
    """Um problema registrado durante uma execução."""

    __tablename__ = "migration_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("migration_runs.id", ondelete="CASCADE"), nullable=False
    )
    row_number: Mapped[int | None] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    field: Mapped[str | None] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Valores já mascarados na origem: documentos completos não são gravados.
    original_value: Mapped[str | None] = mapped_column(String(255))
    normalized_value: Mapped[str | None] = mapped_column(String(255))

    run: Mapped[MigrationRunModel] = relationship(back_populates="issues")


class CustomerModel(Base):
    """Cliente no sistema de destino."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    external_id: Mapped[str | None] = mapped_column(String(60))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str] = mapped_column(String(14), nullable=False)
    document_type: Mapped[str] = mapped_column(String(4), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(13))
    postal_code: Mapped[str | None] = mapped_column(String(8))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    __table_args__ = (Index("ix_customers_document", "document"),)


class ContactModel(Base):
    """Contato vinculado a um cliente pelo documento."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    external_id: Mapped[str | None] = mapped_column(String(60))
    customer_document: Mapped[str] = mapped_column(String(14), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(13))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    __table_args__ = (Index("ix_contacts_customer_document", "customer_document"),)


class InvoiceModel(Base):
    """Cobrança vinculada a um cliente pelo documento."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    external_id: Mapped[str] = mapped_column(String(60), nullable=False)
    customer_document: Mapped[str] = mapped_column(String(14), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    issued_at: Mapped[date] = mapped_column(Date, nullable=False)
    due_at: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    __table_args__ = (Index("ix_invoices_customer_document", "customer_document"),)


__all__ = [
    "MONEY_PRECISION",
    "MONEY_SCALE",
    "Base",
    "ContactModel",
    "CustomerModel",
    "InvoiceModel",
    "MigrationIssueModel",
    "MigrationRunModel",
]
