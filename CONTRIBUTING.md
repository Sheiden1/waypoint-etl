# Como contribuir

Obrigado pelo interesse no Waypoint. Este é um projeto educacional de migração
de dados; contribuições devem favorecer clareza, rastreabilidade e segurança.

## Antes de começar

- leia o `CLAUDE.md` para entender o escopo e o roadmap;
- procure uma issue existente ou abra uma proposta antes de mudanças grandes;
- use somente dados sintéticos em exemplos, testes e screenshots;
- não envie `.env`, uploads, exports, credenciais ou documentos pessoais.

## Ambiente de desenvolvimento

Requisitos: Python 3.12+ e, preferencialmente, `uv`. Para trabalhar na interface
web, Node.js 22.13 ou superior.

```bash
git clone https://github.com/Sheiden1/waypoint-etl.git
cd waypoint-etl
uv sync --extra dev
uv run pre-commit install
uv run python -m waypoint_etl.demo
```

No Windows, os mesmos comandos funcionam no PowerShell. Sem `uv`, crie um
ambiente virtual e execute `pip install -e ".[dev]"`.

### Executar cada interface

Com `make`, em Linux ou macOS:

| Comando            | Ação                                     |
| ------------------ | ---------------------------------------- |
| `make dev`         | interface Streamlit                      |
| `make api`         | API FastAPI                              |
| `make web`         | interface React                          |
| `make docker-up`   | aplicação e PostgreSQL em contêineres    |
| `make docker-down` | encerra os contêineres                   |
| `make demo-data`   | gera os dados sintéticos                 |

Equivalentes sem `make`:

```bash
uv run streamlit run src/waypoint_etl/presentation/streamlit/app.py
uv run uvicorn waypoint_etl.presentation.api.app:app --reload
npm --prefix web install && npm --prefix web run dev
docker compose up --build
```

A interface web precisa da API rodando em paralelo, em outro terminal. Ela usa
`VITE_API_BASE_URL` para saber onde a API está; vazio no desenvolvimento, o Vite
encaminha as chamadas pelo próprio proxy. A documentação interativa da API fica
em `/api/docs`.

### Verificações

```bash
uv run ruff check .
uv run mypy
uv run pytest

npm --prefix web run lint
npm --prefix web run test:run
npm --prefix web run build
```

Testes que dependem de serviços externos são pulados automaticamente quando eles
não estão presentes. Para exercitá-los de verdade:

```bash
# OCR real, com Tesseract instalado
uv run pytest tests/integration/test_ocr_tesseract.py -v

# PostgreSQL real, com um banco de teste descartável
export WAYPOINT_TEST_DATABASE_URL=postgresql+psycopg://waypoint:waypoint@localhost:5432/waypoint_test
uv run pytest tests/integration/test_postgres_load.py -v
```

O CI executa os dois com serviços reais, além de lint, tipos e cobertura mínima.

## Fluxo de trabalho

1. Crie uma branch curta a partir de `main`.
2. Faça a menor alteração suficiente.
3. Adicione testes para toda regra nova ou bug corrigido.
4. Atualize documentação quando o comportamento público mudar.
5. Execute as verificações:

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

Use commits no padrão
[Conventional Commits](https://www.conventionalcommits.org/), por exemplo:

```text
feat(extractors): adiciona suporte a novo delimitador
fix(validators): rejeita vencimento anterior à emissão
docs: esclarece configuração do Tesseract
```

## Arquitetura

- `domain` não depende de Pandas, Streamlit, banco ou OCR;
- `application` coordena casos de uso e contratos;
- `pipeline` contém mapeamento, normalização, validação e deduplicação;
- `infrastructure` implementa extração, OCR, persistência e relatórios;
- `presentation` contém CLI, Streamlit e a API HTTP, sem duplicar regras do
  núcleo — nenhuma rota pode reimplementar transformação ou validação.

Veja [docs/architecture.md](docs/architecture.md) para detalhes.

## Pull requests

Explique o problema, a solução e os comandos usados para validar. PRs devem ser
pequenos, não misturar refatorações sem relação e manter o `dry-run` incapaz de
gravar no banco. O CI precisa passar antes do merge.

Ao contribuir, você concorda em seguir o
[Código de Conduta](CODE_OF_CONDUCT.md).
