"""Status canônico de cobranças."""

from __future__ import annotations

from enum import StrEnum


class InvoiceStatus(StrEnum):
    """Status canônico de uma cobrança (invoice)."""

    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"

    @classmethod
    def from_raw(cls, raw: str) -> InvoiceStatus:
        """Converte um rótulo de origem (pt-BR ou en) para o enum canônico.

        Levanta ``ValueError`` quando o valor não puder ser mapeado, para que a
        validação registre o problema no registro correspondente.
        """
        normalized = (raw or "").strip().lower()
        mapping = {
            "open": cls.OPEN,
            "aberto": cls.OPEN,
            "em aberto": cls.OPEN,
            "pendente": cls.OPEN,
            "paid": cls.PAID,
            "pago": cls.PAID,
            "quitado": cls.PAID,
            "overdue": cls.OVERDUE,
            "vencido": cls.OVERDUE,
            "atrasado": cls.OVERDUE,
            "canceled": cls.CANCELED,
            "cancelled": cls.CANCELED,
            "cancelado": cls.CANCELED,
        }
        try:
            return mapping[normalized]
        except KeyError as exc:
            raise ValueError(f"Status de cobrança desconhecido: {raw!r}") from exc
