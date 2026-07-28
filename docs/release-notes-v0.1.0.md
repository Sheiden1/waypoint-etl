# Waypoint v0.1.0

Primeira versão pública do Waypoint, um toolkit open-source e educacional que
simula uma migração realista entre sistemas ERP e CRM.

## Destaques

- fluxo completo: extrair, mapear, limpar, validar, deduplicar, carregar e auditar;
- CSV, Excel, TXT, DOCX, PDF digital, PDF escaneado e imagens;
- OCR local com Tesseract e fallback por qualidade do texto;
- normalização e validação de dados brasileiros;
- CLI e assistente Streamlit usando o mesmo núcleo;
- `dry-run` seguro e carga transacional opcional no PostgreSQL;
- quatro artefatos por execução, rastreados por `run_id`;
- Docker Compose e CI com PostgreSQL e OCR reais.

## Instalação rápida

```bash
git clone https://github.com/Sheiden1/waypoint-etl.git
cd waypoint-etl
docker compose up --build
```

A interface fica em `http://localhost:8501`.

## Limitações

Esta é uma demonstração técnica, não uma plataforma pronta para dados reais em
produção. Escrita manual, integrações comerciais, autenticação, multitenancy e
processamento distribuído não fazem parte do MVP.

Consulte o [README](../README.md), a
[arquitetura](architecture.md) e a
[política de segurança](../SECURITY.md).
