# Waypoint

> **ERP & CRM Data Migration Toolkit** — Extract. Map. Validate. Migrate.

Projeto pessoal **open-source** que simula uma migração realista de dados entre
sistemas ERP e CRM legados. É uma demonstração técnica e **educacional**: não é
uma plataforma pronta para tratamento de dados reais em produção. O uso com
dados reais exige avaliação própria de segurança, infraestrutura e LGPD.


## O problema

Empresas que trocam de ERP ou CRM recebem dados legados em formatos
incompatíveis: planilhas com cabeçalhos diferentes, datas e valores em formatos
inconsistentes, CPFs/CNPJs com ou sem máscara, clientes duplicados, PDFs e
documentos escaneados. O Waypoint automatiza o fluxo:

**extrair → mapear → limpar → normalizar → validar → deduplicar → revisar →
carregar → auditar.**

## Estado atual

Em desenvolvimento rumo à `v0.1.0`.

- estrutura do projeto em camadas (`domain`, `application`, `infrastructure`,
  `pipeline`, `presentation`);
- configuração de `pyproject.toml`, Ruff, mypy e Pytest;
- núcleo de domínio: entidades canônicas (`Customer`, `Contact`, `Invoice`),
  enums, value objects e validação de dígitos verificadores de CPF/CNPJ;
- gerador de dados sintéticos de demonstração.

## Requisitos

- Python 3.12 ou superior.
- (Opcional) [`uv`](https://github.com/astral-sh/uv) para gerenciar o ambiente.

## Instalação (desenvolvimento)

Com `uv`:

```bash
uv sync --extra dev
```

Sem `uv` (venv + pip):

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```

## Comandos de desenvolvimento

Com `make` (Linux/macOS):

| Comando          | Ação                                   |
| ---------------- | -------------------------------------- |
| `make test`      | executa os testes                      |
| `make lint`      | executa o Ruff                         |
| `make typecheck` | executa o mypy                         |
| `make format`    | formata o código com Ruff              |
| `make demo-data` | gera os dados sintéticos de demonstração |

Equivalentes sem `make` (Windows):

```bash
python -m pytest
python -m ruff check .
python -m mypy
python -m ruff format .
python -m waypoint_etl.demo
```

## Licença

Distribuído sob a licença [MIT](LICENSE).

---

## English summary

**Waypoint** is an open-source, educational toolkit that simulates a realistic
data migration between legacy ERP and CRM systems. It extracts data from
spreadsheets and documents, applies a configurable field mapping, cleans and
normalizes Brazilian data (dates, currency, CPF/CNPJ, phones), validates and
deduplicates records, and produces auditable migration reports. This is a
portfolio/demo project — **not** a production-ready data platform. It is an
independent project and is **not** affiliated with HashiCorp or any other
organization using the *Waypoint* name.
