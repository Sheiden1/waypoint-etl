# Resultados esperados

Os arquivos desta pasta documentam o comportamento esperado para os dados
sintéticos gerados por:

```bash
python -m waypoint_etl.demo
```

`customers-summary.json` registra os totais esperados do pipeline de clientes
CSV. Identificadores de execução e durações não entram no snapshot porque são
gerados a cada execução.

Para conferir:

```bash
waypoint-etl migrate \
  --input samples/input/clientes_legado.csv \
  --mapping mappings/erp_legacy_customers_csv.yaml \
  --output ./exports
```

Compare os totais de `audit-report.json` com o snapshot. Todos os dados são
sintéticos.
