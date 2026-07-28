.PHONY: install dev test lint typecheck format demo-data docker-up docker-down

# Preferimos uv quando disponível; caso contrário, use o venv/pip (ver README).
PYTHON ?= python

install:
	uv sync --extra dev

dev:
	uv run streamlit run src/waypoint_etl/presentation/streamlit/app.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

demo-data:
	$(PYTHON) -m waypoint_etl.demo

docker-up:
	docker compose up -d

docker-down:
	docker compose down
