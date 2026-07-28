"""Criação de engine e sessões do SQLAlchemy.

O sistema precisa iniciar mesmo sem PostgreSQL (seção 21): a ausência de
``DATABASE_URL`` não é erro, apenas restringe a execução ao modo ``dry-run``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ...config import Settings, get_settings
from ...domain.errors import WaypointError
from .models import Base


class DatabaseUnavailableError(WaypointError):
    """Não há banco configurado ou acessível para a operação pedida."""


def create_database_engine(url: str, *, echo: bool = False) -> Engine:
    """Cria a engine para ``url``.

    ``pool_pre_ping`` evita usar conexões derrubadas por timeout, situação comum
    quando a carga acontece bem depois da leitura do arquivo.
    """
    return create_engine(url, echo=echo, pool_pre_ping=True, future=True)


def engine_from_settings(settings: Settings | None = None) -> Engine:
    """Cria a engine a partir da configuração.

    Levanta ``DatabaseUnavailableError`` com orientação quando não há URL, em
    vez de falhar com um erro de conexão obscuro.
    """
    config = settings if settings is not None else get_settings()
    if not config.database_url:
        raise DatabaseUnavailableError(
            "Nenhum banco configurado: defina DATABASE_URL no .env para "
            "carregar os dados. Sem ela, apenas o modo dry-run está disponível."
        )
    return create_database_engine(config.database_url)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Cria a fábrica de sessões ligada à engine."""
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Abre uma sessão transacional.

    Commit ao final, ``rollback`` em qualquer falha: uma carga parcial é pior
    do que uma carga que não aconteceu (seção 15).
    """
    factory = create_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all(engine: Engine) -> None:
    """Cria as tabelas declaradas.

    Atalho para testes e execução local; em produção o schema é responsabilidade
    das migrações Alembic.
    """
    Base.metadata.create_all(engine)


def check_connection(engine: Engine) -> bool:
    """Testa a conexão sem propagar o erro de driver."""
    try:
        with engine.connect():
            return True
    except SQLAlchemyError:
        return False


__all__ = [
    "DatabaseUnavailableError",
    "check_connection",
    "create_all",
    "create_database_engine",
    "create_session_factory",
    "engine_from_settings",
    "session_scope",
]
