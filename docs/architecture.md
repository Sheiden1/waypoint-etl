# Arquitetura

O Waypoint usa um monólito modular em camadas. CLI e Streamlit são adaptadores
de apresentação: ambos chamam os mesmos casos de uso.

```mermaid
flowchart LR
    UI["CLI / Streamlit"] --> APP["application: casos de uso"]
    APP --> PIPE["pipeline ETL"]
    PIPE --> DOMAIN["domain: entidades e regras"]
    APP --> INFRA["infrastructure: extração, OCR, banco e relatórios"]
    INFRA --> DB[("PostgreSQL")]
    INFRA --> FILES["CSV · XLSX · PDF · DOCX · TXT · imagens"]
```

## Responsabilidades

| Camada | Responsabilidade | Não deve conhecer |
| --- | --- | --- |
| `domain` | entidades, enums, value objects e contratos canônicos | Streamlit, SQLAlchemy, Pandas, OCR |
| `application` | DTOs, portas e orquestração de casos de uso | detalhes da interface |
| `pipeline` | mapear, limpar, validar e deduplicar | banco e componentes visuais |
| `infrastructure` | extratores, OCR, PostgreSQL e relatórios | decisões de navegação da interface |
| `presentation` | parâmetros, upload e apresentação de resultados | regras duplicadas do pipeline |

## Fluxo de uma migração

```mermaid
flowchart TD
    A["Detectar formato"] --> B["Extrair"]
    B --> C{"Texto suficiente?"}
    C -->|não| D["OCR"]
    C -->|sim| E["Estruturar"]
    D --> E
    E --> F["Aplicar De/Para"]
    F --> G["Normalizar"]
    G --> H["Validar"]
    H --> I["Deduplicar"]
    I --> J{"dry-run?"}
    J -->|sim| K["Exportar"]
    J -->|não| L["Carga transacional"]
    L --> K
    K --> M["Auditoria por run_id"]
```

Cada linha inválida é isolada e não interrompe o lote. Um erro de infraestrutura
na carga reverte a transação inteira. O `dry-run` é bloqueado antes de qualquer
conexão de escrita.

## Persistência

As tabelas de destino são `customers`, `contacts` e `invoices`. Auditoria usa
`migration_runs` e `migration_issues`. Alembic mantém o schema e lê
`DATABASE_URL` apenas do ambiente.

## Decisões do MVP

- um processo e um banco; sem filas ou microsserviços;
- templates versionáveis em vez de código arbitrário;
- aproximações geram alertas, nunca merge automático;
- documentos enviados não têm armazenamento permanente;
- OCR é um fallback explícito, sempre seguido de validação.
