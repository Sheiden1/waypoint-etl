"""Acesso a banco de dados (SQLAlchemy, Alembic)."""

from .models import (
    Base,
    ContactModel,
    CustomerModel,
    InvoiceModel,
    MigrationIssueModel,
    MigrationRunModel,
)
from .session import (
    DatabaseUnavailableError,
    check_connection,
    create_all,
    create_database_engine,
    engine_from_settings,
    session_scope,
)

__all__ = [
    "Base",
    "ContactModel",
    "CustomerModel",
    "DatabaseUnavailableError",
    "InvoiceModel",
    "MigrationIssueModel",
    "MigrationRunModel",
    "check_connection",
    "create_all",
    "create_database_engine",
    "engine_from_settings",
    "session_scope",
]
