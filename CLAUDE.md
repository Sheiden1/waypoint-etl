# Waypoint

> **Open-source ERP & CRM Data Migration Toolkit**
>
> Extract. Map. Validate. Migrate.

## Identidade do projeto

- **Nome público:** Waypoint
- **Descrição curta:** ERP & CRM Data Migration
- **Repositório:** `waypoint-etl`
- **Distribuição Python:** `waypoint-etl`
- **Módulo Python:** `waypoint_etl`
- **Comando da CLI:** `waypoint-etl`
- **Licença:** MIT

O nome representa os pontos de controle pelos quais os dados passam durante uma
migração: extração, mapeamento, limpeza, validação, revisão e carregamento.

Utilize **Waypoint** na interface e na comunicação pública. Utilize
`waypoint-etl` nos identificadores técnicos para diferenciar o projeto de outros
softwares chamados Waypoint. A documentação deve informar que este é um projeto
open-source independente e sem vínculo com a HashiCorp ou outras organizações
que utilizem o nome Waypoint.

## 1. Instruções para o Claude

Você está trabalhando no **Waypoint**, um projeto open-source de portfólio que simula
um processo real de migração de dados de sistemas ERP e CRM legados.

O projeto deve demonstrar, de forma executável e verificável:

- Python aplicado a ETL;
- extração de dados de CSV, Excel, PDF, Word, TXT e imagens;
- OCR para documentos escaneados;
- mapeamento De/Para configurável;
- limpeza, normalização e validação de dados brasileiros;
- uso prático de Regex;
- identificação de duplicidades;
- persistência em PostgreSQL;
- geração de relatórios de auditoria;
- testes automatizados;
- execução local com Docker;
- documentação suficiente para contribuições open-source.

### Regras obrigatórias de trabalho

1. Antes de alterar qualquer arquivo, examine a estrutura atual do repositório.
2. Implemente uma etapa por vez e preserve tudo que já estiver funcionando.
3. Não adicione funcionalidades fora do escopo do MVP sem registrá-las primeiro no
   roadmap.
4. Não simule funcionalidades na interface. Todo botão visível deve executar uma
   operação real ou estar explicitamente marcado como indisponível.
5. Nunca use dados pessoais reais. Todos os exemplos e fixtures devem ser
   sintéticos.
6. Código, nomes de classes, funções e variáveis devem ser escritos em inglês.
7. Textos da interface e documentação principal devem ser escritos em português
   brasileiro. O README deve conter também um resumo em inglês.
8. Toda nova regra de transformação ou validação deve ter teste automatizado.
9. Antes de considerar uma tarefa concluída, execute testes, lint e verificação de
   tipos.
10. Commits devem ser pequenos, objetivos e usar Conventional Commits.
11. Prefira soluções simples, modulares e legíveis. Não crie microsserviços para o
    MVP.
12. Não grave arquivos enviados ou dados extraídos no Git.
13. Erros de um registro nunca devem interromper o processamento dos demais.
14. Toda migração deve ser rastreável por um identificador `run_id`.
15. O modo `dry-run` nunca pode gravar registros nas tabelas de destino.

---

## 2. Problema que o produto resolve

Empresas que trocam de ERP ou CRM frequentemente recebem dados legados em formatos
incompatíveis com o sistema novo:

- planilhas com cabeçalhos diferentes;
- várias abas e células mescladas;
- datas e valores monetários em formatos inconsistentes;
- CPFs, CNPJs e telefones com ou sem máscara;
- clientes duplicados;
- PDFs digitais;
- fichas cadastrais e contratos escaneados;
- documentos Word;
- arquivos TXT exportados por sistemas antigos.

Esses dados normalmente precisam ser conferidos e corrigidos manualmente antes da
importação. Isso aumenta o tempo de implantação e o risco de informações
incorretas entrarem no sistema de destino.

O Waypoint automatiza o fluxo:

1. extrair;
2. mapear;
3. limpar;
4. normalizar;
5. validar;
6. deduplicar;
7. revisar;
8. carregar;
9. auditar.

---

## 3. Público-alvo

- desenvolvedores responsáveis por migração de sistemas;
- equipes de implantação de ERP e CRM;
- consultorias de dados;
- analistas de integração;
- empresas que precisam preparar arquivos para importação.

O MVP é uma demonstração técnica e não deve ser apresentado como plataforma
pronta para tratamento de dados reais em produção.

---

## 4. Escopo do MVP `v0.1.0`

### Cenário principal

Migrar clientes, contatos e cobranças de um ERP legado fictício para a estrutura
de um CRM fictício.

### Formatos de entrada

- `.csv`;
- `.xlsx`;
- `.pdf` com camada de texto;
- `.pdf` escaneado;
- `.docx`;
- `.txt`;
- `.png`, `.jpg` e `.jpeg`.

### Funcionalidades obrigatórias

- upload pela interface;
- execução equivalente pela CLI;
- detecção do tipo de arquivo;
- extração do conteúdo;
- fallback para OCR quando não houver texto suficiente;
- escolha ou criação de template De/Para;
- prévia dos dados extraídos;
- transformação para um schema canônico;
- limpeza e normalização;
- validação de campos;
- detecção de duplicidades;
- modo `dry-run`;
- exportação dos registros válidos em CSV;
- exportação dos registros rejeitados em XLSX;
- importação opcional dos registros válidos para PostgreSQL;
- relatório JSON de auditoria;
- resumo visual da execução;
- testes automatizados;
- Docker Compose para aplicação e banco;
- pipeline de CI no GitHub Actions.

### Fora do escopo do MVP

- autenticação;
- organizações ou multitenancy;
- cobrança;
- armazenamento permanente dos documentos enviados;
- IA generativa ou uso obrigatório de APIs pagas;
- processamento distribuído;
- filas;
- treinamento próprio de modelo OCR;
- integração direta com ERPs ou CRMs comerciais;
- edição colaborativa;
- permissões por usuário;
- processamento de escrita manual;
- promessa de conformidade jurídica ou regulatória.

Esses itens só poderão entrar após a release `v0.1.0`.

---

## 5. Experiência de uso

### Interface Streamlit

O fluxo principal deve ser um assistente de cinco etapas:

1. **Origem**
   - upload de um ou mais arquivos;
   - identificação do formato;
   - escolha do tipo de dado: clientes, contatos ou cobranças.

2. **Mapeamento**
   - seleção de um template existente;
   - visualização dos campos encontrados;
   - associação dos campos de origem aos campos canônicos;
   - opção de ignorar uma coluna.

3. **Validação**
   - execução do pipeline em `dry-run`;
   - visualização dos registros válidos;
   - visualização dos rejeitados;
   - indicação clara das correções automáticas;
   - indicação de possíveis duplicidades.

4. **Destino**
   - exportar CSV normalizado;
   - exportar XLSX de rejeitados;
   - importar os registros aprovados para PostgreSQL.

5. **Resultado**
   - totais processados, válidos, rejeitados e duplicados;
   - tempo de execução;
   - download do relatório de auditoria;
   - exibição do `run_id`.

### CLI

A CLI deve permitir executar o mesmo núcleo da interface:

```bash
waypoint-etl inspect ./samples/input/clientes_legado.xlsx
```

```bash
waypoint-etl migrate \
  --input ./samples/input/clientes_legado.xlsx \
  --entity customers \
  --mapping ./mappings/erp_legacy_customers.yaml \
  --output ./exports \
  --dry-run
```

```bash
waypoint-etl migrate \
  --input ./samples/input/clientes_legado.xlsx \
  --entity customers \
  --mapping ./mappings/erp_legacy_customers.yaml \
  --output ./exports \
  --load-postgres
```

Não duplique regras entre Streamlit e CLI. As duas interfaces devem chamar os
mesmos casos de uso da camada `application`.

---

## 6. Arquitetura

Utilize um **monólito modular com arquitetura em camadas**.

```mermaid
flowchart TD
    UI["Streamlit ou CLI"] --> APP["Casos de uso"]
    APP --> PIPE["Pipeline ETL"]
    PIPE --> EXT["Extractors e OCR"]
    PIPE --> MAP["Mapping e Cleaning"]
    PIPE --> VAL["Validation e Deduplication"]
    PIPE --> LOAD["Exporters e PostgreSQL"]
    PIPE --> AUDIT["Audit Report"]
```

### Dependências permitidas

- `presentation` depende de `application`;
- `application` depende de `domain`;
- `infrastructure` implementa interfaces definidas no núcleo;
- `domain` não depende de Streamlit, banco, Pandas ou bibliotecas de OCR.

### Pipeline

```mermaid
flowchart TD
    A["Detectar arquivo"] --> B["Extrair conteúdo"]
    B --> C{"Texto suficiente?"}
    C -->|Não| D["Executar OCR"]
    C -->|Sim| E["Estruturar registros"]
    D --> E
    E --> F["Aplicar De/Para"]
    F --> G["Limpar e normalizar"]
    G --> H["Validar"]
    H --> I["Deduplicar"]
    I --> J["Prévia ou persistência"]
    J --> K["Gerar auditoria"]
```

Cada estágio deve receber e devolver objetos explícitos. Evite DataFrames sendo
passados por toda a aplicação sem contratos claros.

---

## 7. Estrutura de diretórios

```text
waypoint-etl/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── architecture.md
│   ├── mapping-guide.md
│   └── screenshots/
├── mappings/
│   ├── erp_legacy_customers.yaml
│   ├── erp_legacy_contacts.yaml
│   └── erp_legacy_invoices.yaml
├── samples/
│   ├── input/
│   └── expected/
├── src/
│   └── waypoint_etl/
│       ├── application/
│       │   ├── dto/
│       │   ├── ports/
│       │   └── use_cases/
│       ├── domain/
│       │   ├── entities/
│       │   ├── enums/
│       │   ├── errors/
│       │   ├── services/
│       │   └── value_objects/
│       ├── infrastructure/
│       │   ├── database/
│       │   ├── extractors/
│       │   ├── loaders/
│       │   ├── ocr/
│       │   ├── repositories/
│       │   └── reports/
│       ├── pipeline/
│       │   ├── cleaners/
│       │   ├── deduplication/
│       │   ├── mappers/
│       │   ├── normalizers/
│       │   └── validators/
│       ├── presentation/
│       │   ├── cli/
│       │   └── streamlit/
│       ├── config.py
│       └── logging.py
├── tests/
│   ├── integration/
│   ├── unit/
│   └── conftest.py
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CLAUDE.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
└── SECURITY.md
```

---

## 8. Stack técnica

### Base

- Python 3.12 ou superior;
- `uv` para dependências e ambiente;
- `pyproject.toml` como fonte de configuração.

### Extração e transformação

- Pandas;
- OpenPyXL;
- pdfplumber;
- python-docx;
- Pillow;
- PyMuPDF para renderização de páginas de PDF quando necessário.

### OCR

- Tesseract OCR instalado no ambiente;
- pytesseract como integração Python;
- OpenCV headless para pré-processamento.

### Validação e dados

- Pydantic;
- Regex da biblioteca padrão;
- SQLAlchemy;
- psycopg;
- PostgreSQL;
- Alembic.

### Interface e CLI

- Streamlit;
- Typer.

### Qualidade

- Pytest;
- Ruff;
- mypy;
- pre-commit;
- GitHub Actions.

Não adicione uma dependência se a biblioteca padrão resolver o problema com
clareza semelhante.

---

## 9. Schemas canônicos

### Customer

```python
class Customer:
    external_id: str | None
    full_name: str
    document: str
    document_type: str
    email: str | None
    phone: str | None
    postal_code: str | None
    city: str | None
    state: str | None
    created_at: datetime | None
```

### Contact

```python
class Contact:
    external_id: str | None
    customer_document: str
    name: str
    role: str | None
    email: str | None
    phone: str | None
```

### Invoice

```python
class Invoice:
    external_id: str
    customer_document: str
    description: str | None
    issued_at: date
    due_at: date
    amount: Decimal
    status: str
```

Valores monetários nunca devem usar `float`.

---

## 10. Mapeamento De/Para

O mapeamento deve ser declarativo e versionável em YAML.

```yaml
version: 1
name: ERP Legado - Clientes
entity: customers

source:
  type: excel
  sheet: Clientes
  header_row: 2

fields:
  Código:
    target: external_id
    required: false

  Nome Cliente:
    target: full_name
    required: true
    transforms:
      - strip
      - collapse_whitespace
      - title_case

  CPF_CNPJ:
    target: document
    required: true
    transforms:
      - digits_only

  Correio Eletrônico:
    target: email
    required: false
    transforms:
      - strip
      - lowercase

  Fone Principal:
    target: phone
    required: false
    transforms:
      - brazilian_phone

  Data Cadastro:
    target: created_at
    required: false
    transforms:
      - brazilian_date

ignored_fields:
  - Observação Interna Antiga
```

O sistema deve falhar com mensagem clara quando:

- o YAML for inválido;
- houver dois campos de origem apontando para o mesmo destino sem estratégia de
  merge;
- um campo obrigatório do schema não tiver origem;
- uma transformação declarada não existir;
- a planilha ou aba informada não existir.

---

## 11. Limpeza, normalização e Regex

Implemente e teste:

- remoção de espaços extras;
- remoção de caracteres de controle;
- normalização Unicode;
- conversão segura de datas brasileiras;
- conversão de moeda brasileira para `Decimal`;
- normalização de CPF e CNPJ;
- normalização de telefone brasileiro;
- normalização de CEP;
- e-mail em lowercase;
- conversão de valores vazios, `N/A`, `NULL`, `-` e equivalentes para `None`.

Regex deve ser utilizada para **extração e reconhecimento de padrões**, não como
substituta para todas as validações.

Padrões mínimos a extrair de texto:

- CPF;
- CNPJ;
- e-mail;
- telefone;
- CEP;
- datas;
- valores em reais.

CPF e CNPJ devem passar também por validação dos dígitos verificadores.

---

## 12. Estratégia de OCR

1. Tente extrair texto nativo do PDF.
2. Calcule uma heurística simples de qualidade:
   - quantidade de caracteres;
   - proporção de caracteres alfanuméricos;
   - presença de padrões esperados.
3. Use OCR somente quando a extração nativa for vazia ou insuficiente.
4. Antes do OCR:
   - converta para escala de cinza;
   - aplique redução de ruído;
   - ajuste o contraste;
   - aplique threshold quando melhorar o resultado.
5. Configure o idioma como português quando os dados necessários estiverem
   instalados.
6. Registre no relatório se o OCR foi utilizado.
7. Nunca trate o resultado do OCR como confiável sem validação posterior.

O MVP precisa processar texto impresso. Escrita manual permanece fora do escopo.

---

## 13. Validações

### Customer

- `full_name` obrigatório e com pelo menos dois caracteres;
- `document` obrigatório;
- CPF ou CNPJ com quantidade e dígitos verificadores válidos;
- e-mail válido quando informado;
- telefone entre 10 e 13 dígitos após normalização;
- UF pertencente ao conjunto oficial de siglas;
- datas futuras de cadastro devem gerar erro.

### Contact

- documento do cliente obrigatório;
- nome obrigatório;
- pelo menos e-mail ou telefone informado.

### Invoice

- identificador externo obrigatório;
- documento do cliente obrigatório;
- emissão e vencimento válidos;
- valor maior ou igual a zero;
- status convertido para enum canônico;
- vencimento anterior à emissão deve gerar erro.

### Severidade

Cada problema deve possuir:

- `code`;
- `message`;
- `field`;
- `severity`: `warning` ou `error`;
- `original_value`;
- `normalized_value`, quando houver.

Um `error` rejeita o registro. Um `warning` permite a importação, mas aparece no
relatório.

---

## 14. Deduplicação

Implemente duas estratégias:

1. **Correspondência exata**
   - CPF/CNPJ;
   - identificador externo;
   - e-mail normalizado.

2. **Possível duplicidade**
   - nome semelhante e mesmo telefone;
   - nome semelhante e mesmo CEP.

Correspondências aproximadas devem apenas gerar alerta. Nunca mescle dois
registros automaticamente no MVP.

---

## 15. Persistência

### Tabelas de destino

- `customers`;
- `contacts`;
- `invoices`.

### Auditoria

- `migration_runs`;
- `migration_issues`.

### MigrationRun

Campos mínimos:

- `id` UUID;
- `status`;
- `entity`;
- `source_filename`;
- `source_hash`;
- `mapping_name`;
- `mapping_version`;
- `dry_run`;
- `total_records`;
- `valid_records`;
- `rejected_records`;
- `duplicate_records`;
- `ocr_used`;
- `started_at`;
- `finished_at`;
- `duration_ms`.

Não armazene o conteúdo original completo do documento no banco por padrão.

Carregamentos reais devem usar transação. Se ocorrer erro de infraestrutura
durante a carga, reverta a transação e preserve o relatório da tentativa.

---

## 16. Relatório de auditoria

Cada execução deve produzir:

```text
exports/<run_id>/
├── accepted.csv
├── rejected.xlsx
├── duplicates.csv
└── audit-report.json
```

O `audit-report.json` deve registrar:

- metadados da execução;
- hash do arquivo;
- template utilizado;
- quantidade por resultado;
- transformações aplicadas;
- alertas;
- erros;
- uso ou não de OCR;
- duração por estágio;
- versão do Waypoint.

Não inclua segredos, strings de conexão ou stack traces sensíveis.

---

## 17. Observabilidade e erros

- use logging estruturado;
- inclua `run_id` nos logs;
- não use `print` no núcleo da aplicação;
- mensagens apresentadas ao usuário devem sugerir uma ação;
- stack traces ficam apenas nos logs de desenvolvimento;
- um arquivo inválido deve gerar uma falha controlada;
- uma linha inválida deve ser enviada para rejeitados sem parar o lote;
- calcule a duração de cada estágio do pipeline.

---

## 18. Segurança e privacidade

- somente dados sintéticos no repositório;
- validar extensão e conteúdo do arquivo;
- limitar tamanho do upload;
- impedir path traversal;
- gerar nomes internos seguros;
- processar uploads em diretório temporário;
- remover temporários ao fim da execução;
- não executar macros de planilhas ou documentos;
- não registrar os valores completos de documentos pessoais nos logs;
- mascarar CPF/CNPJ em mensagens de auditoria apresentadas na interface;
- manter `.env`, uploads e exports fora do versionamento.

O README deve explicar que o projeto é educacional e que o uso com dados reais
exige avaliação própria de segurança, infraestrutura e LGPD.

---

## 19. Testes

### Unitários

- normalizadores;
- parsers de datas e moeda;
- extração por Regex;
- validação de CPF e CNPJ;
- validação de schemas;
- carregamento do YAML;
- aplicação das transformações;
- deduplicação.

### Integração

- Excel para registros canônicos;
- PDF digital para registros canônicos;
- imagem para OCR e extração;
- pipeline completo em `dry-run`;
- pipeline completo com PostgreSQL;
- geração dos quatro arquivos de saída.

### Regressão

Crie fixtures pequenas para cada bug corrigido.

### Critério mínimo

- testes determinísticos;
- nenhuma chamada de rede;
- banco de teste isolado;
- cobertura mínima inicial de 80% sobre `domain`, `pipeline` e `application`;
- CI executando lint, tipos e testes.

---

## 20. Comandos de desenvolvimento esperados

```bash
make install
make dev
make test
make lint
make typecheck
make format
make docker-up
make docker-down
make demo-data
```

O projeto deve funcionar também sem `make`, com os comandos equivalentes
documentados no README para usuários de Windows.

---

## 21. Variáveis de ambiente

Forneça `.env.example` sem segredos:

```dotenv
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://waypoint:waypoint@localhost:5432/waypoint
MAX_UPLOAD_MB=25
TESSERACT_CMD=
OCR_LANGUAGE=por
EXPORT_DIR=./exports
```

O sistema deve iniciar em modo somente `dry-run` mesmo quando o PostgreSQL não
estiver disponível. A carga para banco deve informar claramente a ausência da
conexão.

---

## 22. Dados de demonstração

Gere um conjunto sintético contendo:

- 50 clientes;
- CPFs e CNPJs de teste gerados programaticamente;
- diferentes máscaras;
- datas em pelo menos três formatos;
- valores monetários brasileiros;
- cinco registros duplicados;
- cinco documentos inválidos;
- três e-mails inválidos;
- campos vazios;
- caracteres especiais e espaços extras;
- uma planilha com duas abas;
- um PDF digital;
- um PDF escaneado;
- um DOCX;
- um TXT.

Não use documentos que possam pertencer a pessoas reais.

Inclua os resultados esperados em `samples/expected/` para permitir verificação.

---

## 23. Plano de implementação em 12 dias

### Dia 1 — Fundação ✅ (concluído)

- [x] criar estrutura;
- [x] configurar `pyproject.toml`;
- [x] configurar Ruff, mypy e Pytest;
- [x] criar modelos de domínio;
- [x] gerar dados sintéticos.

> Estrutura em camadas criada; núcleo de domínio (entidades, enums, value
> objects com validação de dígitos verificadores de CPF/CNPJ), `config.py`,
> `logging.py` e gerador de dados sintéticos (`python -m waypoint_etl.demo`)
> implementados. Ruff, mypy (strict) e Pytest verdes; cobertura do `domain`
> ~99%.

### Dia 2 — Dados tabulares ✅ (concluído)

- [x] extrator CSV;
- [x] extrator Excel;
- [x] suporte a abas e cabeçalho configurável;
- [x] testes.

> Contratos da extração em `application/dto/extraction.py` (`ExtractionOptions`,
> `SourceRecord`, `ExtractionResult`) e port `Extractor` em
> `application/ports/`. `CsvExtractor` (stdlib `csv`, detecção de codificação e
> delimitador) e `ExcelExtractor` (openpyxl somente leitura, sem macros) em
> `infrastructure/extractors/`, com `detect_format`/`get_extractor` por
> extensão. Toda célula vira texto bruto ou `None`; linhas curtas, longas ou em
> branco não interrompem o lote e cada registro guarda o número da linha de
> origem. Planilha de demonstração com duas abas e cabeçalho na linha 2 gerada
> por `make demo-data`. 124 testes verdes; Ruff e mypy (strict) limpos.

### Dia 3 — Documentos ✅ (concluído)

- [x] extrator TXT;
- [x] extrator DOCX;
- [x] extrator PDF digital;
- [x] testes.

> Documentos não têm linhas e colunas, então ganharam contrato próprio:
> `DocumentText`/`PageText` em `application/dto/document.py` e o port
> `DocumentExtractor` (o antigo `Extractor` virou `TabularExtractor`).
> `TxtExtractor` reaproveita a detecção de codificação do CSV; `DocxExtractor`
> percorre o corpo na ordem original, preservando o par rótulo/valor de
> parágrafos e tabelas; `PdfExtractor` lê apenas o texto nativo e registra em
> `empty_pages` as páginas sem camada de texto, deixando a decisão de OCR para
> o Dia 8. O registry passou a distinguir fontes tabulares de documentos, com
> mensagens que orientam qual extrator usar. Fixtures TXT, DOCX e PDF digital
> gerados por `make demo-data`. 167 testes verdes; Ruff e mypy (strict) limpos;
> cobertura 90%.

### Dia 4 — De/Para ✅ (concluído)

- [x] schema YAML;
- [x] parser;
- [x] catálogo de transformações;
- [x] mensagens de erro;
- [x] testes.

> `MappingTemplate`/`FieldMapping`/`SourceSpec` em `pipeline/mappers/schema.py`
> e o parser em `loader.py`, cobrindo as cinco falhas da seção 10 com mensagem
> acionável. O catálogo de transformações é **fechado**: um template escolhe
> entre funções auditáveis, nunca executa código arbitrário. `SourceSpec` passa
> a alimentar o `ExtractionOptions`, então aba e `header_row` deixam de ser
> informados na mão. `apply_mapping` falha antes de processar qualquer linha
> quando faltam colunas — template errado é erro de configuração, não lote
> rejeitado. Templates em `mappings/` para as três entidades.

### Dia 5 — Limpeza ✅ (concluído)

- [x] datas;
- [x] moeda;
- [x] documentos;
- [x] telefones;
- [x] e-mails;
- [x] Regex;
- [x] testes.

> Implementado **antes** do Dia 4, porque o catálogo de transformações depende
> dele. `pipeline/normalizers/`: texto (controle, Unicode NFC, marcadores
> nulos, `title_case` com partículas), datas brasileiras (dia antes do mês, e
> `None` em vez de adivinhar), moeda em `Decimal` (nunca `float`), documento,
> telefone e CEP (recupera o zero à esquerda perdido pela planilha).
> `pipeline/cleaners/patterns.py` extrai CPF, CNPJ, e-mail, telefone, CEP,
> datas e valores de texto livre — com os documentos conferidos pelos dígitos
> verificadores, para não confundir protocolo com CPF.

### Dia 6 — Qualidade ✅ (concluído)

- [x] validações;
- [x] severidades;
- [x] rejeitados;
- [x] deduplicação;
- [x] testes.

> `Issue` (domínio) com `code`, `message`, `field`, `severity`,
> `original_value` e `normalized_value`, além de `for_display()`, que mascara
> CPF/CNPJ para a auditoria (seção 18). Validadores das três entidades
> devolvem **todos** os problemas de uma vez e produzem a entidade canônica
> quando o registro é válido. Deduplicação exata (documento, identificador
> externo, e-mail) e aproximada (nome semelhante + telefone ou CEP), que apenas
> alerta: o MVP nunca mescla registros.

### Dia 7 — Banco ✅ (concluído)

- [x] PostgreSQL;
- [x] SQLAlchemy;
- [x] Alembic;
- [x] transações;
- [x] teste de integração.

> Modelos das cinco tabelas (`customers`, `contacts`, `invoices`,
> `migration_runs`, `migration_issues`) com tipos **portáveis**, o que permite
> exercitar o comportamento transacional real contra SQLite sem subir um banco.
> `MigrationRun` carrega todos os campos da seção 15, com `run_id` UUID e hash
> SHA-256 do arquivo de origem. `load_records` barra o `dry-run` **antes** de
> qualquer conexão (regra 15) e a carga é atômica: erro de infraestrutura
> reverte o lote inteiro. Issues são gravadas já mascaradas. Migração Alembic
> inicial validada aplicando-a de verdade.
>
> ⚠️ O teste contra PostgreSQL real existe em
> `tests/integration/test_postgres_load.py`, mas **não foi executado**: exige
> `WAYPOINT_TEST_DATABASE_URL`. Pendente para a seção 26.

### Dia 8 — OCR ✅ (concluído, com ressalva)

- [x] Tesseract;
- [x] pré-processamento com OpenCV;
- [x] fallback automático;
- [x] fixture escaneada;
- [x] testes.

> O fallback é um **decorador** (`DocumentExtractorWithOcr`), não uma alteração
> do `PdfExtractor`: o extrator segue puro e testável sem Tesseract, e o custo
> de rasterizar páginas fica explícito em quem monta o pipeline. A heurística da
> seção 12 vive em `pipeline/cleaners/text_quality.py` e combina contagem de
> caracteres, proporção alfanumérica e presença de padrões esperados — um CPF
> legível basta para dispensar o OCR. Só as páginas insuficientes são
> processadas, e o uso do OCR sempre vira aviso no relatório. `ImageExtractor`
> fecha o último formato do MVP. Fixtures escaneados (PDF sem camada de texto e
> PNG) gerados por `make demo-data`.
>
> ⚠️ Toda a lógica de decisão é testada com um motor falso e determinístico,
> mas o **OCR real não foi executado**: o Tesseract não está instalado neste
> ambiente. `tests/integration/test_ocr_tesseract.py` cobre esse caminho e é
> pulado automaticamente. A seção 26 exige rodá-lo antes da release.

### Dia 9 — CLI ✅ (concluído)

- [x] `inspect`;
- [x] `migrate`;
- [x] `dry-run`;
- [x] exportações.

> O trabalho real foi criar os **casos de uso** (`inspect_source` e
> `run_migration`): a CLI só monta parâmetros e apresenta o `MigrationResult`,
> então o Streamlit do Dia 10 consome exatamente o mesmo núcleo (seção 5).
> `StageTimer` mede os seis estágios do pipeline e o `audit-report.json` é
> escrito **depois** que a exportação fecha, para registrar a própria duração.
> Os quatro artefatos da seção 16 saem em `exports/<run_id>/`. `migrate` sai com
> código 1 quando há rejeitados, permitindo uso em verificação automatizada.
>
> Três defeitos apareceram ao rodar a CLI de verdade e foram corrigidos:
> `title_case` destruía formas jurídicas ("ALMEIDA S/A" virava "Almeida S/a");
> a ausência de `DATABASE_URL` vazava stack trace em vez de mensagem; e aplicar
> um template de Excel a um CSV falhava com "coluna não encontrada" em vez de
> apontar a divergência de formato. Daí também nasceu
> `mappings/erp_legacy_customers_csv.yaml`.

### Dia 10 — Streamlit ✅ (concluído)

- [x] upload;
- [x] mapeamento;
- [x] prévia;
- [x] resultados;
- [x] downloads.

> Assistente real de cinco etapas em
> `presentation/streamlit/app.py`, consumindo os mesmos casos de uso da CLI.
> Uploads são limitados por `MAX_UPLOAD_MB`, têm o nome saneado, vivem somente
> em diretório temporário e são removidos ao fim de cada operação. A origem
> aceita todos os formatos do MVP para inspeção; CSV e Excel seguem para o
> pipeline estruturado.
>
> O De/Para pode ser escolhido no catálogo, enviado como YAML ou criado
> visualmente pela associação de cada coluna a um campo canônico. A validação
> sempre começa em `dry-run`; os quatro artefatos têm downloads reais, e a
> carga PostgreSQL só aparece quando `DATABASE_URL` está configurada e exige
> confirmação explícita. Prévia de válidos, issues e duplicidades mascara
> CPF/CNPJ. `make dev` inicia a interface. Teste smoke do app e testes do
> adaptador cobrem os fluxos; 503 testes verdes, Ruff e mypy (strict) limpos.

### Dia 11 — Open source ✅ (concluído)

- [x] Docker;
- [x] GitHub Actions;
- [x] documentação;
- [x] contribuição;
- [x] licença MIT;
- [x] segurança.

> Imagem Python 3.12 com Tesseract e idioma português, usuário sem privilégios,
> healthcheck e interface Streamlit. O Compose sobe PostgreSQL com volume,
> espera o banco ficar saudável, aplica Alembic e só então inicia o app. O CI
> executa Ruff, mypy strict, cobertura mínima de 80%, testes com Tesseract e
> PostgreSQL reais, build da distribuição e um segundo job que constrói e testa
> o Compose.
>
> Adicionados guia de contribuição, código de conduta, política de segurança,
> changelog, templates de issue/PR, pre-commit, arquitetura e guia De/Para. A
> licença MIT existente foi preservada. A validação local alcançou 95% de
> cobertura; Docker será comprovado pelo runner Linux porque não está instalado
> nesta máquina.

### Dia 12 — Publicação (em conclusão)

- [x] revisão completa;
- [ ] release `v0.1.0`;
- [x] screenshots;
- [x] GIF ou vídeo;
- [x] README em português com resumo em inglês;
- [ ] publicação no LinkedIn.

> A revisão de release encontrou e corrigiu a ligação ausente do Tesseract nas
> interfaces: CLI e Streamlit agora instanciam o motor real ao inspecionar
> imagens e PDFs. A fixture CSV versionada possui snapshot esperado com 55
> registros, 45 válidos, 10 rejeitados e 4 duplicatas. Foram criadas duas
> capturas vetoriais, um vídeo MP4 curto, notas da release e o texto pronto para
> LinkedIn em `docs/linkedin-v0.1.0.md`.
>
> A tag depende do CI verde no GitHub. A publicação no LinkedIn permanece como
> ação externa: não há conector disponível nesta sessão, mas o conteúdo está
> pronto para copiar e publicar.

---

## 24. Roadmap posterior

### `v0.2.0`

- histórico visual de execuções;
- templates criados pela interface;
- API REST opcional;
- comparação entre origem e destino;
- reconciliação pós-migração;
- exportação de relatório em PDF.

### `v0.3.0`

- sistema de plugins para extractors;
- adaptadores demonstrativos de CRM;
- execução em lotes maiores;
- regras customizadas por template;
- métricas Prometheus.

Não implemente o roadmap antes do MVP estar concluído.

---

## 25. Documentação open-source

O repositório deve conter:

- `README.md`: problema, demonstração, instalação, uso, arquitetura e limitações;
- `CONTRIBUTING.md`: configuração, branches, testes e pull requests;
- `CODE_OF_CONDUCT.md`;
- `SECURITY.md`: relato responsável de vulnerabilidades;
- `CHANGELOG.md`;
- licença MIT;
- templates de issue;
- template de pull request;
- labels sugeridas: `good first issue`, `bug`, `enhancement`, `documentation`,
  `help wanted`.

O README deve apresentar o projeto honestamente como:

> Projeto pessoal open-source que simula uma migração realista de dados entre
> sistemas ERP e CRM.

Não afirmar que o projeto realizou migrações comerciais reais.

---

## 26. Definition of Done da `v0.1.0`

A primeira versão só estará pronta quando:

- todos os formatos declarados tiverem ao menos uma fixture funcional;
- OCR for executado de verdade em um documento escaneado;
- o template YAML controlar o mapeamento;
- registros inválidos forem isolados;
- duplicidades forem identificadas;
- `dry-run` não alterar o banco;
- a carga no PostgreSQL funcionar em transação;
- os quatro relatórios forem gerados;
- Streamlit e CLI usarem o mesmo núcleo;
- Docker Compose iniciar aplicação e banco;
- CI estiver verde;
- testes, lint e tipos passarem;
- dados de demonstração forem inteiramente sintéticos;
- README permitir que outra pessoa execute o projeto;
- licença e arquivos de contribuição estiverem presentes;
- a release `v0.1.0` estiver criada.

---

## 27. Ordem obrigatória para cada implementação

Ao receber uma solicitação de desenvolvimento:

1. explique em uma frase qual parte do pipeline será afetada;
2. inspecione os arquivos relacionados;
3. proponha a menor mudança suficiente;
4. implemente o domínio ou contrato;
5. implemente a infraestrutura necessária;
6. adicione ou atualize testes;
7. execute testes específicos;
8. execute a suíte completa quando apropriado;
9. atualize documentação quando o comportamento público mudar;
10. resuma o que foi concluído e o que permanece pendente.

Se uma decisão não estiver definida neste documento, escolha a alternativa mais
simples que preserve rastreabilidade, testabilidade e facilidade de contribuição.
