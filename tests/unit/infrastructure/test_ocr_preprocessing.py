"""Testes do pré-processamento de imagem antes do OCR (seção 12, item 4)."""

from __future__ import annotations

import numpy as np
import pytest

from waypoint_etl.demo.document_files import render_form_image
from waypoint_etl.infrastructure.ocr.preprocessing import (
    PreprocessingOptions,
    binarize,
    decode_image,
    denoise,
    encode_png,
    enhance_contrast,
    preprocess,
    to_grayscale,
)


@pytest.fixture
def scan_bytes() -> bytes:
    """Uma ficha "digitalizada" em PNG."""
    import io

    image = render_form_image()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_decode_and_encode_round_trip(scan_bytes: bytes) -> None:
    image = decode_image(scan_bytes)

    assert image.ndim == 3
    assert encode_png(image).startswith(b"\x89PNG")


def test_decode_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="decodificar"):
        decode_image(b"isto nao e uma imagem")


def test_to_grayscale_reduces_to_one_channel(scan_bytes: bytes) -> None:
    gray = to_grayscale(decode_image(scan_bytes))

    assert gray.ndim == 2


def test_to_grayscale_is_idempotent(scan_bytes: bytes) -> None:
    gray = to_grayscale(decode_image(scan_bytes))

    assert to_grayscale(gray).shape == gray.shape


def test_denoise_removes_salt_and_pepper() -> None:
    """Ruído pontual é o defeito típico de digitalização."""
    clean = np.full((60, 60), 255, dtype=np.uint8)
    noisy = clean.copy()
    noisy[::7, ::7] = 0

    restored = denoise(noisy)

    assert np.count_nonzero(restored == 0) < np.count_nonzero(noisy == 0)


def test_enhance_contrast_widens_the_histogram() -> None:
    flat = np.full((80, 80), 120, dtype=np.uint8)
    flat[40:, :] = 130

    enhanced = enhance_contrast(flat)

    assert np.ptp(enhanced) >= np.ptp(flat)


def test_binarize_produces_only_black_and_white(scan_bytes: bytes) -> None:
    gray = to_grayscale(decode_image(scan_bytes))

    binary = binarize(gray)

    assert set(np.unique(binary)).issubset({0, 255})


def test_preprocess_returns_png(scan_bytes: bytes) -> None:
    result = preprocess(scan_bytes)

    assert result.startswith(b"\x89PNG")
    assert decode_image(result).size > 0


def test_preprocess_steps_can_be_disabled(scan_bytes: bytes) -> None:
    options = PreprocessingOptions(
        grayscale=False, denoise=False, enhance_contrast=False, threshold=False
    )

    result = preprocess(scan_bytes, options)

    assert decode_image(result).ndim == 3


def test_threshold_alone_still_converts_to_grayscale(scan_bytes: bytes) -> None:
    """CLAHE e limiar exigem um canal só: a conversão não pode ser esquecida."""
    options = PreprocessingOptions(
        grayscale=False, denoise=False, enhance_contrast=False, threshold=True
    )

    result = preprocess(scan_bytes, options)

    assert set(np.unique(to_grayscale(decode_image(result)))).issubset({0, 255})


def test_preprocessing_is_deterministic(scan_bytes: bytes) -> None:
    assert preprocess(scan_bytes) == preprocess(scan_bytes)
