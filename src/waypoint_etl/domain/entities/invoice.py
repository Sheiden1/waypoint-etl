"""Entidade canônica Invoice (cobrança)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..enums.invoice_status import InvoiceStatus


@dataclass(frozen=True, slots=True)
class Invoice:
    """Cobrança no schema canônico de destino.

    Valores monetários usam ``Decimal`` — nunca ``float`` (seção 9).
    """

    external_id: str
    customer_document: str
    issued_at: date
    due_at: date
    amount: Decimal
    status: InvoiceStatus
    description: str | None = None
