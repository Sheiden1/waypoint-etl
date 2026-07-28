# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-07-28

### Adicionado

- extração de CSV, Excel, TXT, DOCX, PDF e imagens;
- fallback de OCR com Tesseract para PDFs escaneados e imagens;
- templates De/Para declarativos e validados em YAML;
- normalização de texto, datas, moeda, CPF/CNPJ, telefone, CEP e e-mail;
- validação de clientes, contatos e cobranças com severidades;
- deduplicação exata e identificação de possíveis duplicidades;
- execução compartilhada pela CLI e pelo assistente Streamlit;
- modo `dry-run`, exportações e relatório JSON de auditoria por `run_id`;
- persistência transacional em PostgreSQL com Alembic;
- dados de demonstração inteiramente sintéticos;
- Docker Compose com aplicação, PostgreSQL e Tesseract;
- CI com lint, tipos, cobertura, OCR real e PostgreSQL real;
- documentação e arquivos de comunidade para colaboração open-source.

### Segurança

- uploads temporários com nome saneado e limite configurável;
- documentos mascarados em issues e prévias de auditoria;
- segredos, uploads e exports excluídos do versionamento.

[0.1.0]: https://github.com/Sheiden1/waypoint-etl/releases/tag/v0.1.0
