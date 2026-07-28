"""Smoke test da página Streamlit."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.integration

APP = Path("src/waypoint_etl/presentation/streamlit/app.py")


def test_app_starts_in_dry_run_mode_without_database() -> None:
    app = AppTest.from_file(str(APP), default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value.endswith("Waypoint")
    assert any("Envie um arquivo" in message.value for message in app.info)
    assert len(app.file_uploader) == 1
