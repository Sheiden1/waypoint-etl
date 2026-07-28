# Guia de mapeamento De/Para

Templates ligam colunas legadas ao schema canônico. Eles são YAML versionável e
nunca executam código arbitrário.

## Estrutura mínima

```yaml
version: 1
name: ERP Legado - Clientes CSV
entity: customers

source:
  type: csv
  header_row: 1

fields:
  Nome Cliente:
    target: full_name
    required: true
    transforms:
      - clean_text
      - title_case

  CPF_CNPJ:
    target: document
    required: true
    transforms:
      - digits_only

ignored_fields:
  - Observação Interna
```

## Origem

`source.type` pode ser `csv` ou `excel` no pipeline estruturado. Excel também
aceita `sheet`; `header_row` começa em 1. CSV pode declarar `encoding` e
`delimiter`.

## Entidades e campos obrigatórios

| Entidade | Campos obrigatórios |
| --- | --- |
| `customers` | `full_name`, `document` |
| `contacts` | `customer_document`, `name` |
| `invoices` | `external_id`, `customer_document`, `issued_at`, `due_at`, `amount`, `status` |

Os demais campos estão definidos em
`src/waypoint_etl/domain/services/canonical_schema.py`.

## Transformações

Transformações comuns:

- `clean_text`, `strip`, `collapse_whitespace`, `title_case`;
- `lowercase`, `uppercase`, `email`;
- `digits_only`, `brazilian_phone`, `postal_code`, `uf`;
- `brazilian_date`, `brazilian_money`.

A ordem importa. Conversões de data e moeda são finalizadas durante a validação
para que valores inválidos virem issues do registro.

## Erros de configuração

O template falha antes de processar registros quando:

- o YAML ou a versão são inválidos;
- falta origem para campo canônico obrigatório;
- duas colunas apontam para o mesmo destino;
- o destino ou a transformação não existe;
- o tipo de origem diverge do arquivo;
- a aba ou uma coluna declarada não existe.

Use `waypoint-etl inspect` para confirmar formato, abas e cabeçalho antes da
migração. Na interface Streamlit, o template também pode ser criado visualmente
e baixado para versionamento.
