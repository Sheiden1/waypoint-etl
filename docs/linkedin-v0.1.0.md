# Texto sugerido para o LinkedIn

🧭 Hoje publiquei a primeira versão do Waypoint, meu projeto pessoal open-source
de migração de dados entre sistemas ERP e CRM.

O objetivo foi transformar um problema comum de implantação — arquivos legados
inconsistentes — em um fluxo executável e auditável:

extrair → mapear → limpar → normalizar → validar → deduplicar → revisar →
carregar → auditar.

Nesta `v0.1.0`, o projeto processa CSV, Excel, TXT, DOCX, PDFs digitais,
documentos escaneados e imagens. Ele inclui OCR com Tesseract, templates De/Para
em YAML, validações de dados brasileiros, detecção de duplicidades, `dry-run`,
PostgreSQL, CLI, interface Streamlit, Docker Compose e CI.

Cada execução recebe um `run_id` e gera arquivos separados para registros
aceitos, rejeitados, duplicidades e auditoria.

Foi também um exercício prático de arquitetura em camadas, testes automatizados,
tipagem estática, transações e documentação para colaboração open-source.

O projeto é educacional e usa somente dados sintéticos — não é apresentado como
uma plataforma pronta para dados reais em produção.

Código e demonstração:
https://github.com/Sheiden1/waypoint-etl

#Python #ETL #DataEngineering #OpenSource #PostgreSQL #Streamlit #OCR
#DataMigration
