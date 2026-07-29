# Deploy gratuito da plataforma web

> Verificado em 28 de julho de 2026. Planos e limites mudam; consulte as
> referências oficiais no fim deste documento antes de publicar uma nova
> versão.

Esta configuração publica apenas a SPA React/Vite no Vercel Hobby e executa a
API FastAPI em um Web Service Free do Render. O PostgreSQL do Neon é opcional:
sem `DATABASE_URL`, inspeção, mapeamento, validação e downloads continuam
funcionando, mas a carga persistente fica indisponível.

```text
Navegador
   │
   ├── HTTPS ──> Vercel Hobby ──> React/Vite estático
   │
   └── HTTPS ──> Render Free ───> FastAPI + pipeline + OCR
                                      │
                                      └── Neon Free (opcional)
```

O projeto continua sendo uma demonstração open-source para uso pessoal e não
comercial. Não envie dados pessoais reais: o arquivo sai do navegador e é
processado na infraestrutura do Render.

## Arquivos de infraestrutura

| Arquivo | Responsabilidade |
| --- | --- |
| `web/vercel.json` | build Vite, saída `dist` e fallback de SPA |
| `render.yaml` | Web Service Docker Free, variáveis e health check |
| `Dockerfile.api` | imagem Python, Tesseract, migrações e Uvicorn |
| `scripts/smoke_deployment.py` | teste público de frontend, API, CORS e pipeline |

Este repositório funciona como monorepo:

- no **Vercel**, configure **Root Directory** como `web`;
- no **Render**, mantenha a raiz do repositório. O `render.yaml`, o
  `Dockerfile.api`, `src/` e `alembic/` estão nessa raiz.

## 1. Publicar a API no Render Free

1. Envie o repositório para um provedor Git aceito pelo Render.
2. No Dashboard do Render, escolha **New > Blueprint** e conecte o repositório.
3. Confirme o arquivo `render.yaml` na raiz.
4. Quando o Blueprint solicitar `WEB_ORIGINS`, informe temporariamente
   `http://localhost:5173`. A origem pública exata será corrigida depois do
   primeiro deploy do Vercel.
5. Crie o Blueprint e aguarde o health check ficar saudável.
6. Copie a URL pública final, por exemplo
   `https://waypoint-etl-api.onrender.com`.

O Blueprint fixa:

- runtime Docker e plano `free`;
- região `virginia`;
- imagem construída por `Dockerfile.api`;
- health check em `/api/v1/health`;
- deploy automático somente depois que os checks do commit passarem;
- Uvicorn em `0.0.0.0` e na porta fornecida por `PORT`;
- um único processo, adequado aos 512 MB de RAM do plano gratuito.

Teste inicial:

```powershell
$ApiUrl = "https://SEU-SERVICO.onrender.com"
Invoke-RestMethod "$ApiUrl/api/v1/health"
```

A primeira resposta pode levar cerca de um minuto porque o serviço gratuito
entra em repouso quando fica ocioso.

## 2. Publicar o frontend no Vercel Hobby

1. No Vercel, escolha **Add New > Project** e importe o mesmo repositório.
2. Em **Root Directory**, selecione `web`.
3. O preset deve ser **Vite**. O `web/vercel.json` já define:
   `npm ci`, `npm run build`, saída `dist` e rewrite para `index.html`.
4. Em **Environment Variables**, crie:

   ```text
   VITE_API_BASE_URL=https://SEU-SERVICO.onrender.com
   ```

   Aplique pelo menos a **Production**. Para testar deployments de Preview,
   aplique também a **Preview**.
5. Faça o deploy e copie a URL de produção exata, por exemplo
   `https://waypoint-etl.vercel.app`.

`VITE_API_BASE_URL` é incorporada aos arquivos JavaScript durante o build. Ela
é pública e não deve conter segredo. Alterar seu valor exige um novo deploy do
frontend.

## 3. Fechar o CORS entre os dois serviços

No Render, abra **waypoint-etl-api > Environment**, altere `WEB_ORIGINS` para a
origem de produção exata do Vercel e salve:

```text
https://SEU-PROJETO.vercel.app
```

Uma origem contém protocolo, host e porta opcional, sem caminho e sem barra
final. Para autorizar também um domínio próprio, separe valores por vírgula:

```text
https://SEU-PROJETO.vercel.app,https://waypoint.exemplo.dev
```

Cada deployment de Preview do Vercel recebe uma origem diferente. A interface
abre normalmente, mas chamadas à API serão bloqueadas pelo navegador até que
essa origem específica seja adicionada a `WEB_ORIGINS`. Não use `*` para
contornar isso.

## 4. Neon Free opcional

Ignore esta seção se o objetivo for apenas inspecionar, validar e baixar
artefatos.

1. Crie um projeto no Neon Free.
2. No modal **Connect**, copie duas URLs:
   - conexão **pooled**, indicada para a aplicação web;
   - conexão **direct**, indicada para migrações de schema.
3. Troque somente o prefixo `postgresql://` por
   `postgresql+psycopg://`, preservando usuário, senha, host, banco e
   parâmetros TLS.
4. No Render, adicione manualmente como variáveis secretas:

   ```text
   DATABASE_URL=postgresql+psycopg://...-pooler.../neondb?sslmode=require
   DATABASE_DIRECT_URL=postgresql+psycopg://.../neondb?sslmode=require
   ```

5. Solicite um novo deploy do serviço.

Na inicialização, `Dockerfile.api` executa `alembic upgrade head` com
`DATABASE_DIRECT_URL`; em seguida, a aplicação usa a conexão pooled de
`DATABASE_URL`. Se apenas `DATABASE_URL` existir, a mesma URL será usada para
as migrações. Nunca versione essas strings.

O Neon Free atual oferece 0,5 GB de armazenamento e 100 CU-horas mensais por
projeto, com scale-to-zero após inatividade. O primeiro acesso depois da
suspensão pode ter latência adicional.

## Variáveis

### Render

| Variável | Obrigatória | Valor ou função |
| --- | --- | --- |
| `APP_ENV` | sim | `production` |
| `LOG_LEVEL` | sim | `INFO` |
| `MAX_UPLOAD_MB` | sim | `25`; reduza se houver pressão de memória |
| `OCR_LANGUAGE` | sim | `por`, instalado na imagem |
| `EXPORT_DIR` | sim | `/tmp/waypoint-exports`, sempre efêmero |
| `MAPPINGS_DIR` | sim | `/app/mappings`, catálogo copiado para a imagem |
| `ARTIFACT_TTL_SECONDS` | sim | `1800`; janela temporária dos downloads |
| `WEB_ORIGINS` | sim | origens HTTPS exatas, separadas por vírgula |
| `DATABASE_URL` | não | Neon pooled com driver `psycopg` |
| `DATABASE_DIRECT_URL` | não | Neon direct para Alembic |

Não configure `PORT`: o Render a fornece. O comando da imagem usa `10000`
apenas como fallback local.

### Vercel

| Variável | Obrigatória | Valor ou função |
| --- | --- | --- |
| `VITE_API_BASE_URL` | sim | URL HTTPS pública do serviço Render, sem barra final |

## Smoke test reproduzível

Depois de corrigir o CORS, execute a partir da raiz do repositório:

```powershell
python scripts/smoke_deployment.py `
  --web-url https://SEU-PROJETO.vercel.app `
  --api-url https://SEU-SERVICO.onrender.com
```

Em Linux ou macOS:

```bash
python scripts/smoke_deployment.py \
  --web-url https://SEU-PROJETO.vercel.app \
  --api-url https://SEU-SERVICO.onrender.com
```

O teste usa somente a biblioteca padrão e os dados sintéticos versionados. Ele
verifica:

1. HTML da SPA;
2. `GET /api/v1/health`;
3. preflight CORS da origem informada;
4. catálogo versionado de mapeamentos;
5. upload e inspeção de `clientes_legado.csv`;
6. pipeline real em `dry-run`;
7. presença, TTL e download dos quatro artefatos.

O timeout padrão por requisição é 120 segundos para tolerar o cold start do
Render. Qualquer falha encerra o processo com código diferente de zero.

## Limitações dos planos gratuitos

### Vercel Hobby

- uso pessoal e não comercial, sujeito à política de fair use;
- um build concorrente no Hobby;
- até 100 deployments por dia e 45 minutos por build;
- em deploy via CLI, até 100 MB de arquivos-fonte enviados;
- ao atingir limites gratuitos, recursos normalmente ficam indisponíveis até
  a janela de uso ser renovada.

Esta arquitetura usa o Vercel apenas para arquivos estáticos; a aplicação não
consome Vercel Functions.

### Render Free

- 512 MB de RAM e 0,1 CPU; OCR de PDFs grandes pode ser lento ou exceder a
  memória;
- repouso após 15 minutos sem tráfego e retorno em aproximadamente um minuto;
- 750 horas gratuitas por workspace a cada mês;
- filesystem efêmero, apagado em reinícios, novos deploys e suspensões;
- sem disco persistente, SSH, one-off jobs ou escala acima de uma instância;
- limites mensais de banda e minutos de build também se aplicam;
- o serviço é público, sem autenticação ou rate limit no MVP.

O desaparecimento de uploads e exportações temporárias é esperado. Os
downloads devem ser feitos na mesma jornada. Mesmo usando instâncias Free, o
Render pode cobrar excedentes de banda ou pipeline quando há um método de
pagamento cadastrado. Para impedir cobrança automática, não cadastre um método
de pagamento: segundo o Render, o serviço ou os novos builds serão suspensos
ao esgotar a franquia. Acompanhe o painel de uso durante o mês.

### Neon Free

- banco opcional; sem ele o health check informa `database: false`;
- 0,5 GB e 100 CU-horas mensais por projeto na oferta consultada;
- scale-to-zero obrigatório no Free, com possível latência no primeiro acesso;
- conexão pooled para a aplicação e direct para operações administrativas e
  migrações.

## Diagnóstico rápido

| Sintoma | Verificação |
| --- | --- |
| A interface mostra API indisponível | confira `VITE_API_BASE_URL` e refaça o deploy do Vercel |
| Erro de CORS no console | copie a origem exata para `WEB_ORIGINS` e reinicie o Render |
| `502` ou espera longa no primeiro acesso | aguarde o cold start e consulte logs/health check |
| Deploy Render não abre porta | confirme que `PORT` não foi sobrescrita |
| OCR aparece indisponível | confirme que o deploy usou `Dockerfile.api` |
| Catálogo de mapeamentos vazio | confira `MAPPINGS_DIR`; o pacote instalado não carrega os YAML |
| Push não dispara deploy no Render | com repo importado por URL, sem GitHub App, `checksPass` não vê os checks; use Manual Deploy ou instale a integração |
| Smoke test recebe `302` do frontend | use o alias canônico de produção; URLs por deployment e por branch caem no SSO do Deployment Protection |
| Banco aparece indisponível | confira `DATABASE_URL` no ambiente do Render |
| Migração falha com pooler | configure também `DATABASE_DIRECT_URL` |
| Processo encerra ao ler PDF/imagem | reduza `MAX_UPLOAD_MB`; 512 MB é o limite do Free |

## Referências oficiais

- [Vercel: Vite](https://vercel.com/docs/frameworks/frontend/vite)
- [Vercel: monorepos](https://vercel.com/docs/monorepos)
- [Vercel: configuração de build](https://vercel.com/docs/builds/configure-a-build)
- [Vercel: plano Hobby](https://vercel.com/docs/plans/hobby)
- [Vercel: limites](https://vercel.com/docs/limits)
- [Render: Web Services](https://render.com/docs/web-services)
- [Render: Blueprint YAML](https://render.com/docs/blueprint-spec)
- [Render: planos gratuitos](https://render.com/docs/free)
- [Render: FAQ de cobrança](https://render.com/docs/faq)
- [Render: tipos de instância](https://render.com/docs/compute-plans)
- [Render: health checks](https://render.com/docs/health-checks)
- [Neon: preços e limites](https://neon.com/pricing)
- [Neon: connection pooling](https://neon.com/docs/connect/connection-pooling)
