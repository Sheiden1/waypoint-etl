FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        tesseract-ocr \
        tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install .

COPY alembic.ini ./
COPY alembic ./alembic
COPY mappings ./mappings

RUN groupadd --system waypoint \
    && useradd --system --gid waypoint --home-dir /app waypoint \
    && mkdir -p /app/exports \
    && chown -R waypoint:waypoint /app

USER waypoint

EXPOSE 8501

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)"

CMD ["streamlit", "run", "src/waypoint_etl/presentation/streamlit/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
