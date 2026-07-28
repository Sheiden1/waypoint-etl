.PHONY: install dev api web web-install web-build web-test test lint typecheck format demo-data docker-up docker-down

# Preferimos uv quando disponível; caso contrário, use o venv/pip (ver README).
PYTHON ?= python

install:
	uv sync --extra dev

dev:
	uv run streamlit run src/waypoint_etl/presentation/streamlit/app.py

api:
	uv run uvicorn waypoint_etl.presentation.api.app:app --reload

web:
	npm --prefix web run dev

web-install:
	npm --prefix web install

web-build:
	npm --prefix web run build

web-test:
	npm --prefix web run test:run

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
