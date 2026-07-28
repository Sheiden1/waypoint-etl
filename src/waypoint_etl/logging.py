"""Logging estruturado com suporte a ``run_id``.

Regras (seção 17 do CLAUDE.md):

- não usar ``print`` no núcleo da aplicação;
- incluir ``run_id`` nos logs quando disponível;
- stack traces ficam apenas nos logs de desenvolvimento.
"""

from __future__ import annotations

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formata registros de log como uma linha JSON.

    Anexa o ``run_id`` quando presente no registro (via ``extra``).
    """

    _RESERVED = frozenset(logging.makeLogRecord({}).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        run_id = getattr(record, "run_id", None)
        if run_id is not None:
            payload["run_id"] = str(run_id)

        # Campos adicionais passados via `extra`.
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configura o logging global da aplicação em formato JSON."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(
    name: str, *, run_id: str | None = None
) -> logging.LoggerAdapter[logging.Logger]:
    """Retorna um logger que injeta automaticamente o ``run_id`` nos registros."""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {"run_id": run_id} if run_id else {})
