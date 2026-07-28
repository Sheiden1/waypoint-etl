"""Schema inicial: tabelas de destino e de auditoria.

Revision ID: 0001
Revises:
Create Date: 2024-01-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY_PRECISION = 18
MONEY_SCALE = 2


def upgrade() -> None:
    op.create_table(
        "migration_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("entity", sa.String(length=20), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("mapping_name", sa.String(length=120), nullable=True),
        sa.Column("mapping_version", sa.Integer(), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("total_records", sa.Integer(), nullable=False),
        sa.Column("valid_records", sa.Integer(), nullable=False),
        sa.Column("rejected_records", sa.Integer(), nullable=False),
        sa.Column("duplicate_records", sa.Integer(), nullable=False),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "migration_issues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("field", sa.String(length=60), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("original_value", sa.String(length=255), nullable=True),
        sa.Column("normalized_value", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["migration_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=60), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.String(length=14), nullable=False),
        sa.Column("document_type", sa.String(length=4), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=13), nullable=True),
        sa.Column("postal_code", sa.String(length=8), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customers_document", "customers", ["document"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=60), nullable=True),
        sa.Column("customer_document", sa.String(length=14), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=13), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contacts_customer_document", "contacts", ["customer_document"]
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=60), nullable=False),
        sa.Column("customer_document", sa.String(length=14), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=False),
        sa.Column("due_at", sa.Date(), nullable=False),
        sa.Column(
            "amount", sa.Numeric(precision=MONEY_PRECISION, scale=MONEY_SCALE),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_invoices_customer_document", "invoices", ["customer_document"]
    )


def downgrade() -> None:
    op.drop_index("ix_invoices_customer_document", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_contacts_customer_document", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_customers_document", table_name="customers")
    op.drop_table("customers")
    op.drop_table("migration_issues")
    op.drop_table("migration_runs")
