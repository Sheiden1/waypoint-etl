.PHONY: install dev test lint typecheck format demo-data docker-up docker-down

# Preferimos uv quando disponível; caso contrário, use o venv/pip (ver README).
PYTHON ?= python

install:
	uv sync --extra dev

# A interface Streamlit chega no Dia 10 do plano. Até lá o alvo falha de forma
# explícita, no mesmo padrão dos comandos indisponíveis da CLI.
dev:
	@echo "Interface Streamlit indisponivel nesta versao (prevista para o Dia 10)."
	@echo "Use a CLI: uv run waypoint-etl --help"
	@exit 1

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
