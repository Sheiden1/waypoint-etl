"""Integração com o Tesseract OCR via pytesseract.

O binário do Tesseract é um requisito **externo**: ele não vem com o pacote
Python. Por isso o motor expõe ``is_available()`` e o restante do sistema trata
a ausência como uma limitação conhecida, nunca como uma falha silenciosa.
"""

from __future__ import annotations

import io
from functools import lru_cache

import pytesseract
from PIL import Image

from ...config import Settings, get_settings
from ...domain.errors import WaypointError
from .preprocessing import PreprocessingOptions, preprocess


class OcrUnavailableError(WaypointError):
    """O Tesseract não está instalado ou não foi encontrado no PATH."""


class TesseractEngine:
    """Motor de OCR baseado no Tesseract."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        preprocessing: PreprocessingOptions | None = None,
    ) -> None:
        self._settings = settings if settings is not None else get_settings()
        self._preprocessing = preprocessing or PreprocessingOptions()
        if self._settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self._settings.tesseract_cmd

    @property
    def name(self) -> str:
        return "tesseract"

    @property
    def language(self) -> str:
        """Idioma configurado (``por`` por padrão, conforme seção 21)."""
        return self._settings.ocr_language

    def is_available(self) -> bool:
        """Indica se o binário do Tesseract responde neste ambiente."""
        return _tesseract_version(self._settings.tesseract_cmd) is not None

    def image_to_text(self, image: bytes) -> str:
        """Pré-processa a imagem e extrai o texto.

        Levanta ``OcrUnavailableError`` quando o binário não está instalado, com
        instrução de instalação em vez de um ``TesseractNotFoundError`` cru.
        """
        if not self.is_available():
            raise OcrUnavailableError(
                "Tesseract OCR não encontrado. Instale o binário e, se preciso, "
                "aponte TESSERACT_CMD no .env para o executável."
            )

        prepared = preprocess(image, self._preprocessing)
        with Image.open(io.BytesIO(prepared)) as handle:
            text = pytesseract.image_to_string(handle, lang=self._resolved_language())
        return str(text)

    def _resolved_language(self) -> str:
        """Usa o idioma configurado, caindo para inglês se não estiver instalado.

        Os dados de idioma do Tesseract são instalados separadamente; pedir um
        idioma ausente falharia a execução inteira (seção 12, item 5).
        """
        available = _available_languages(self._settings.tesseract_cmd)
        if self.language in available:
            return self.language
        return "eng"


@lru_cache(maxsize=4)
def _tesseract_version(command: str | None) -> str | None:
    """Versão do Tesseract, ou ``None`` quando indisponível (memoizado)."""
    try:
        return str(pytesseract.get_tesseract_version())
    except Exception:
        # pytesseract levanta TesseractNotFoundError, mas também erros de OS
        # quando o caminho configurado está errado.
        return None


@lru_cache(maxsize=4)
def _available_languages(command: str | None) -> frozenset[str]:
    """Idiomas instalados no Tesseract deste ambiente."""
    try:
        return frozenset(pytesseract.get_languages(config=""))
    except Exception:
        return frozenset()


__all__ = ["OcrUnavailableError", "TesseractEngine"]
