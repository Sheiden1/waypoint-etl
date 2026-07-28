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
| `make dev`       | interface Streamlit (indisponível até o Dia 10)  |

Equivalentes sem `make` (Windows):

```bash
python -m pytest
python -m ruff check .
python -m mypy
python -m ruff format .
python -m waypoint_etl.demo
```

## Dados de demonstração

`make demo-data` (ou `python -m waypoint_etl.demo`) escreve em `samples/input/`:

| Arquivo                 | Conteúdo                                                     |
| ----------------------- | ------------------------------------------------------------ |
| `clientes_legado.csv`   | clientes legados com máscaras, datas e sujeira variadas       |
| `clientes_legado.xlsx`  | abas `Clientes` (cabeçalho na linha 2) e `Contatos`           |
| `clientes_legado.txt`   | relatório em texto puro no estilo de exportação antiga        |
| `ficha_cadastral.docx`  | fichas em Word, com parágrafos e tabelas rótulo/valor         |
| `ficha_cadastral.pdf`   | fichas em PDF com camada de texto (uma por página)            |
| `ficha_escaneada.pdf`   | PDF **sem** camada de texto, para exercitar o OCR              |
| `ficha_escaneada.png`   | ficha como imagem digitalizada                                |

Todos os registros são sintéticos e gerados com semente fixa: nenhum dado
pessoal real é usado ou versionado.

Os arquivos binários (`.xlsx`, `.docx` e `.pdf`) não são versionados — gere-os
com `make demo-data` após clonar o repositório.

## Mapeamento De/Para

O mapeamento entre as colunas de origem e o schema canônico é declarado em YAML
e versionado em `mappings/`:

| Template                       | Entidade    |
| ------------------------------ | ----------- |
| `erp_legacy_customers.yaml`    | `customers` |
| `erp_legacy_contacts.yaml`     | `contacts`  |
| `erp_legacy_invoices.yaml`     | `invoices`  |

O bloco `source` diz como ler o arquivo (aba, linha do cabeçalho, delimitador) e
cada campo declara o destino canônico e as transformações aplicadas:

```yaml
fields:
  CPF_CNPJ:
    target: document
    required: true
    transforms:
      - digits_only
```

As transformações vêm de um catálogo fechado: um template escolhe entre funções
conhecidas e auditáveis, nunca executa código arbitrário. Um nome inexistente
faz o carregamento falhar listando as opções válidas.

## Requisitos externos

Duas funcionalidades dependem de programas que **não** vêm com as dependências
Python. A ausência de qualquer um deles não impede o projeto de rodar — apenas
limita o que está disponível, sempre com mensagem explícita:

| Recurso        | Sem ele                                                       |
| -------------- | ------------------------------------------------------------- |
| **PostgreSQL** | só o modo `dry-run`; exportações continuam funcionando         |
| **Tesseract**  | PDFs escaneados e imagens não são lidos (os demais formatos sim) |

Para o OCR, instale o Tesseract e, se ele não estiver no `PATH`, aponte
`TESSERACT_CMD` no `.env`. O pacote de idioma português (`por`) é recomendado;
sem ele o Waypoint cai para o inglês em vez de falhar.

Os testes que dependem desses serviços são pulados automaticamente quando eles
não estão presentes:

```bash
# OCR real (exige o Tesseract instalado)
uv run pytest tests/integration/test_ocr_tesseract.py -v

# PostgreSQL real (exige um banco de teste descartável)
export WAYPOINT_TEST_DATABASE_URL=postgresql+psycopg://waypoint:waypoint@localhost:5432/waypoint_test
uv run pytest tests/integration/test_postgres_load.py -v
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
