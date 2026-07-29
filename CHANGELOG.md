# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o
versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.2.0] - 2026-07-29

### Adicionado

- jornada web em React, TypeScript e Astryx, cobrindo as cinco etapas do fluxo
  sem depender do Streamlit: origem, mapeamento, validação, destino e resultado;
- API FastAPI como borda HTTP fina sobre os casos de uso existentes, com
  catálogo de templates, `dry-run`, carga confirmada e download dos artefatos;
- relatórios temporários por `run_id`, com lista permitida de nomes e TTL
  configurável por `ARTIFACT_TTL_SECONDS`;
- preferências de tema, densidade e movimento, com contrato tipado para temas
  comunitários;
- estruturação de documentos (TXT, DOCX, PDF e imagem) em registros canônicos
  por reconhecimento de pares `Rótulo: valor`, declarada no bloco `source` do
  template; documentos passam a percorrer o mesmo pipeline de uma planilha,
  incluindo validação, deduplicação e os quatro artefatos;
- templates versionados para TXT e DOCX;
- instância pública gratuita: interface no Vercel Hobby e API no Render Free,
  validadas pelo smoke test remoto em `scripts/smoke_deployment.py`;
- `MAPPINGS_DIR` para localizar o catálogo De/Para independentemente do layout
  de instalação do pacote.

### Alterado

- coluna ausente no template só bloqueia quando o destino é obrigatório no
  schema canônico ou quando o template declara `required: true`; as demais
  passam a gerar aviso e o campo fica sem origem;
- o flag `required` do YAML passa a valer em execução — antes era lido e nunca
  consultado.

### Corrigido

- catálogo de templates De/Para vinha vazio sempre que o pacote era instalado
  (imagem Docker da API e do Streamlit): o caminho padrão era derivado da árvore
  de fontes, que não existe em `site-packages`;
- a versão exposta pelo OpenAPI estava fixa em `0.1.0`, divergindo do pacote.

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

[0.2.0]: https://github.com/Sheiden1/waypoint-etl/releases/tag/v0.2.0
[0.1.0]: https://github.com/Sheiden1/waypoint-etl/releases/tag/v0.1.0
