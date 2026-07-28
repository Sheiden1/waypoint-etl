"""Pré-processamento de imagem antes do OCR (seção 12, item 4).

A ordem segue a receita da seção 12: escala de cinza, redução de ruído, ajuste
de contraste e binarização. Cada etapa é isolada para poder ser testada e
desligada individualmente — threshold, em especial, piora imagens já limpas.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Núcleo do CLAHE: 8x8 é o padrão do OpenCV e funciona bem para documentos A4.
_CLAHE_TILE_SIZE = (8, 8)
_CLAHE_CLIP_LIMIT = 2.0

# Janela do filtro de mediana; 3 remove ruído de digitalização sem borrar texto.
_MEDIAN_BLUR_KERNEL = 3

# Binarização adaptativa: melhor que limiar fixo quando a iluminação do
# documento escaneado é irregular.
_ADAPTIVE_BLOCK_SIZE = 31
_ADAPTIVE_CONSTANT = 10


@dataclass(frozen=True, slots=True)
class PreprocessingOptions:
    """Quais etapas aplicar antes do OCR."""

    grayscale: bool = True
    denoise: bool = True
    enhance_contrast: bool = True
    threshold: bool = True


def decode_image(data: bytes) -> np.ndarray:
    """Decodifica bytes de imagem em uma matriz do OpenCV."""
    buffer = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Não foi possível decodificar a imagem.")
    return image


def encode_png(image: np.ndarray) -> bytes:
    """Codifica a matriz de volta em PNG."""
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Não foi possível codificar a imagem em PNG.")
    return bytes(buffer.tobytes())


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Converte para escala de cinza, se ainda não estiver."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise(image: np.ndarray) -> np.ndarray:
    """Remove ruído pontual preservando as bordas das letras."""
    return cv2.medianBlur(image, _MEDIAN_BLUR_KERNEL)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Equaliza o contraste localmente (CLAHE).

    Equalização global apagaria texto claro em uma região escura da página.
    """
    clahe = cv2.createCLAHE(clipLimit=_CLAHE_CLIP_LIMIT, tileGridSize=_CLAHE_TILE_SIZE)
    return clahe.apply(image)


def binarize(image: np.ndarray) -> np.ndarray:
    """Aplica limiar adaptativo, tolerando iluminação irregular."""
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        _ADAPTIVE_BLOCK_SIZE,
        _ADAPTIVE_CONSTANT,
    )


def preprocess(
    data: bytes, options: PreprocessingOptions | None = None
) -> bytes:
    """Aplica o pré-processamento e devolve a imagem em PNG."""
    opts = options or PreprocessingOptions()
    image = decode_image(data)

    # CLAHE e limiar adaptativo só operam em um canal: se qualquer um deles
    # estiver ligado, a conversão para cinza é obrigatória.
    if opts.grayscale or opts.enhance_contrast or opts.threshold:
        image = to_grayscale(image)
    if opts.denoise:
        image = denoise(image)
    if opts.enhance_contrast:
        image = enhance_contrast(image)
    if opts.threshold:
        image = binarize(image)

    return encode_png(image)


__all__ = [
    "PreprocessingOptions",
    "binarize",
    "decode_image",
    "denoise",
    "encode_png",
    "enhance_contrast",
    "preprocess",
    "to_grayscale",
]
