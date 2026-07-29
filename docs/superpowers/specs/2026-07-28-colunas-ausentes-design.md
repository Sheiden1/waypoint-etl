# Colunas ausentes no template De/Para

> Desenho validado em 28 de julho de 2026.

## Problema

Ao aplicar um template, `apply_mapping` falha se **qualquer** coluna declarada
faltar no arquivo, sem distinguir a natureza da ausência. Isso trata dois casos
muito diferentes como o mesmo erro:

- falta `Correio Eletrônico`, um campo opcional que aquele export simplesmente
  não trouxe — situação normal, que hoje impede a migração inteira;
- falta `CPF_CNPJ`, a identidade do registro — situação em que continuar
  produziria dados inúteis.

Arquivos reais quase sempre divergem do template em alguma coluna opcional, e a
rigidez atual obriga a editar o YAML a cada variação de export.

## Estado atual

Existem duas noções de obrigatoriedade e apenas uma é aplicada em execução.

| Onde | Regra | Aplicada? |
| --- | --- | --- |
| `loader.py:304` | o template precisa declarar origem para todo campo obrigatório do schema canônico | sim |
| `mapper.py:56` | toda coluna declarada precisa existir no arquivo | sim, sem distinguir obrigatória de opcional |
| `required:` no YAML (`FieldMapping.required`) | marca um campo como obrigatório | **não** — o valor é lido, exposto pela API e nunca consultado no pipeline |

O motor já tolera coluna ausente: `map_record` usa `record.values.get(...)`, que
devolve `None`, aplica `default` quando houver e deixa a decisão para os
validadores. Só a guarda em `apply_mapping` impede o fluxo.

Os avisos do mapeamento já trafegam até o resultado final: `run_migration.py:141`
concatena `mapped.warnings`, que alimentam `audit-report.json` e o campo
`warnings` da resposta HTTP, já tipado no frontend.

## Regra proposta

Uma coluna ausente **bloqueia a execução** se, e somente se:

1. o destino é obrigatório no schema canônico da entidade
   (`full_name` e `document` para clientes), **ou**
2. o template declara `required: true` para aquele campo.

Qualquer outra ausência é tolerada: o campo fica nulo e um aviso é registrado.

A segunda condição torna o flag do YAML honesto. Quem escreve um template ganha
um controle real — pode exigir `email` para o seu caso de negócio, mesmo que o
schema canônico não exija. Nenhum dos quatro templates versionados muda de
comportamento, porque neles `required: true` já coincide com os campos
obrigatórios do schema.

## Componentes

### `pipeline/mappers/schema.py`

`MappingTemplate.missing_columns()` é substituído por duas consultas. O dataclass
já carrega `entity`, então pode consultar `required_field_names(entity)` do
domínio — dependência permitida, porque `pipeline` depende de `domain`.

```python
missing_blocking_columns(available)   # obrigatórias: erro
missing_tolerable_columns(available)  # opcionais: aviso
```

### `pipeline/mappers/mapper.py`

`apply_mapping` levanta `MappingError` apenas para as bloqueantes, preservando a
falha antes de processar qualquer linha. As toleráveis entram em
`MappingResult.warnings` com mensagem que nomeia as colunas e o efeito
("ficarão vazias"). `map_record` não muda.

### `presentation/api`

Nenhuma mudança de contrato. Os avisos já são serializados.

### `web/src/features/mapping/MappingWorkspace.tsx`

Hoje um único aviso amarelo cobre qualquer ausência. Passa a distinguir três
estados, calculados a partir do template e das colunas do arquivo:

| Situação | Selo | Mensagem |
| --- | --- | --- |
| nenhuma ausente | `Compatível` | — |
| só opcionais ausentes | `Campos vazios` (aviso) | "Estas colunas não existem no arquivo e ficarão vazias: …" |
| alguma obrigatória ausente | `Incompatível` (erro) | "Este template não serve para este arquivo. Faltam colunas obrigatórias: …" |

O terceiro caso cobre a escolha de template errado, que hoje aparece como
"arquivo incompleto" e desorienta. O botão de avançar continua sem bloqueio: o
backend permanece a fonte da verdade.

## Testes

Unitários em `tests/unit/pipeline/`:

- coluna opcional ausente: executa, campo canônico nulo, aviso presente;
- coluna canônica obrigatória ausente: `MappingError` antes de mapear qualquer
  linha;
- coluna marcada `required: true` no YAML, opcional no schema canônico, ausente:
  `MappingError` — comportamento novo do flag;
- os quatro templates versionados mantêm comportamento idêntico.

Componente em `web/src/features/mapping/`: os três estados do selo.

## Fora de escopo

- não inventar nem inferir valores para colunas ausentes;
- não oferecer "ignorar tudo": forçar a ausência de campo obrigatório produziria
  registros sem identidade, contrariando o propósito da ferramenta;
- não criar heurística de "template provavelmente errado" por proporção de
  colunas ausentes — os campos obrigatórios já ancoram essa detecção;
- não expor controle de linha de cabeçalho na interface web (limitação separada,
  registrada durante a Fase 6).
