# Waypoint

> **ERP & CRM Data Migration Toolkit** — Extract. Map. Validate. Migrate.

[![CI](https://github.com/Sheiden1/waypoint-etl/actions/workflows/ci.yml/badge.svg)](https://github.com/Sheiden1/waypoint-etl/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)

Projeto pessoal **open-source** que simula uma migração realista de dados entre
sistemas ERP e CRM legados. É uma demonstração técnica e **educacional**: não é
uma plataforma pronta para tratamento de dados reais em produção. O uso com
dados reais exige avaliação própria de segurança, infraestrutura e LGPD.

O Waypoint é um projeto independente, sem vínculo com a HashiCorp ou qualquer
outra organização que use o nome Waypoint.

![Resultado de uma validação no Waypoint](docs/screenshots/waypoint-result.svg)

[▶ Assista à demonstração curta](docs/demo/waypoint-demo.mp4)

## O problema

Empresas que trocam de ERP ou CRM recebem dados legados em formatos
incompatíveis: planilhas com cabeçalhos diferentes, datas e valores em formatos
inconsistentes, CPFs/CNPJs com ou sem máscara, clientes duplicados, PDFs e
documentos escaneados. O Waypoint automatiza o fluxo:

**extrair → mapear → limpar → normalizar → validar → deduplicar → revisar →
carregar → auditar.**

## Recursos da v0.1.0

- CSV, Excel, TXT, DOCX, PDF digital, PDF escaneado e imagens;
- OCR local com Tesseract e fallback por qualidade do texto;
- templates De/Para em YAML ou criados visualmente;
- normalização e validação de dados brasileiros;
- detecção de duplicidades exatas e possíveis;
- CLI e assistente Streamlit usando o mesmo núcleo;
- `dry-run`, PostgreSQL transacional e auditoria por `run_id`;
- exportação de aceitos, rejeitados, duplicidades e relatório JSON;
- Docker Compose, testes automatizados, Ruff, mypy e CI.

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

## Início rápido com Docker

Com Docker e Docker Compose instalados:

```bash
git clone https://github.com/Sheiden1/waypoint-etl.git
cd waypoint-etl
docker compose up --build
```

Acesse `http://localhost:8501`. O Compose inicia PostgreSQL, aplica as migrações
Alembic e sobe a interface com Tesseract e o idioma português instalados.

```bash
docker compose down
```

Use `docker compose down -v` somente quando quiser também apagar os volumes
locais do banco e das exportações.

## Comandos de desenvolvimento

Com `make` (Linux/macOS):

| Comando          | Ação                                   |
| ---------------- | -------------------------------------- |
| `make test`      | executa os testes                      |
| `make lint`      | executa o Ruff                         |
| `make typecheck` | executa o mypy                         |
| `make format`    | formata o código com Ruff              |
| `make demo-data` | gera os dados sintéticos de demonstração |
| `make dev`       | inicia a interface Streamlit             |
| `make docker-up` | inicia aplicação e PostgreSQL             |
| `make docker-down` | encerra os containers                   |

Equivalentes sem `make` (Windows):

```bash
python -m pytest
python -m ruff check .
python -m mypy
python -m ruff format .
python -m waypoint_etl.demo
uv run streamlit run src/waypoint_etl/presentation/streamlit/app.py
docker compose up --build
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

## Uso pela interface

Inicie o assistente web:

```bash
make dev
```

No Windows, sem `make`:

```powershell
uv run streamlit run src/waypoint_etl/presentation/streamlit/app.py
```

O assistente percorre cinco etapas: upload e inspeção, De/Para, validação em
`dry-run`, downloads ou carga opcional no PostgreSQL e resumo da execução. O
De/Para pode vir do catálogo em `mappings/`, de um YAML enviado ou ser criado
pela associação visual das colunas. Os quatro artefatos continuam sendo
gravados em `exports/<run_id>/`.

## Uso pela CLI

Inspecionar um arquivo antes de migrar:

```bash
uv run waypoint-etl inspect samples/input/clientes_legado.xlsx --sheet Clientes --header-row 2
```

Executar a migração em `dry-run` (padrão — nada é gravado no banco):

```bash
uv run waypoint-etl migrate \
  --input samples/input/clientes_legado.xlsx \
  --mapping mappings/erp_legacy_customers.yaml \
  --output ./exports
```

Cada execução gera `exports/<run_id>/` com os quatro artefatos de auditoria:

| Arquivo             | Conteúdo                                              |
| ------------------- | ----------------------------------------------------- |
| `accepted.csv`      | registros válidos, no schema canônico                  |
| `rejected.xlsx`     | uma linha por problema, com os valores de origem       |
| `duplicates.csv`    | duplicatas exatas e suspeitas                          |
| `audit-report.json` | metadados, totais, duração por estágio e alertas       |

O comando sai com código `1` quando há registros rejeitados, o que permite usá-lo
em verificação automatizada. Para efetivar a carga no PostgreSQL:

```bash
uv run waypoint-etl migrate ... --no-dry-run --load-postgres
```

## Mapeamento De/Para

O mapeamento entre as colunas de origem e o schema canônico é declarado em YAML
e versionado em `mappings/`:

| Template                        | Entidade    | Origem  |
| ------------------------------- | ----------- | ------- |
| `erp_legacy_customers.yaml`     | `customers` | Excel   |
| `erp_legacy_customers_csv.yaml` | `customers` | CSV     |
| `erp_legacy_contacts.yaml`      | `contacts`  | Excel   |
| `erp_legacy_invoices.yaml`      | `invoices`  | CSV     |

Um template declara o formato da origem: aplicá-lo a outro formato falha com
mensagem explícita, porque o `header_row` de uma planilha desalinharia a leitura
de um CSV.

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

Consulte o [guia completo de mapeamento](docs/mapping-guide.md).

## Arquitetura

```mermaid
flowchart LR
    UI["CLI / Streamlit"] --> APP["Casos de uso"]
    APP --> PIPE["Pipeline ETL"]
    PIPE --> DOMAIN["Domínio"]
    APP --> INFRA["Extração · OCR · PostgreSQL · relatórios"]
```

O projeto é um monólito modular em camadas. O domínio não depende de interface,
banco ou OCR; Streamlit e CLI apenas montam parâmetros e apresentam os mesmos
objetos de resultado. Veja [docs/architecture.md](docs/architecture.md).

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

No CI, ambos são executados de verdade: o runner instala Tesseract e usa um
serviço PostgreSQL descartável.

## Limitações

- o pipeline estruturado do MVP migra CSV e Excel; documentos são inspecionados
  e extraídos, mas ainda não viram múltiplos registros canônicos automaticamente;
- escrita manual não é suportada;
- não há autenticação, multitenancy, filas ou integrações com ERPs comerciais;
- possíveis duplicidades não são mescladas automaticamente;
- documentos enviados não têm armazenamento permanente;
- uso com dados reais exige avaliação própria de segurança e LGPD.

## Contribuição e segurança

Leia [CONTRIBUTING.md](CONTRIBUTING.md), o
[Código de Conduta](CODE_OF_CONDUCT.md) e a
[Política de Segurança](SECURITY.md). Bugs e melhorias podem ser abertos pelos
templates de issue. Vulnerabilidades devem usar o relato privado do GitHub.

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
