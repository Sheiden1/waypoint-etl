"""Configuração da aplicação carregada a partir do ambiente (.env).

Fica na raiz do pacote (fora de `domain`) porque depende de bibliotecas de
infraestrutura. O sistema deve iniciar em modo somente ``dry-run`` mesmo quando
o PostgreSQL não estiver disponível.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação.

    Todos os valores possuem padrões seguros para execução local em modo
    ``dry-run``, de forma que a ausência de um ``.env`` não impeça a inicização.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str | None = None
    max_upload_mb: int = Field(default=25, ge=1)
    tesseract_cmd: str | None = None
    ocr_language: str = "por"
    export_dir: Path = Path("./exports")

    @property
    def database_available(self) -> bool:
        """Indica se há uma URL de banco configurada.

        A carga real para o PostgreSQL só deve ser tentada quando ``True``.
        """
        return bool(self.database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna as configurações (memoizadas) da aplicação."""
    return Settings()
