# Changelog

Todas as mudanças notáveis neste projeto serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

---

## [0.1.0] — 2026-11-10

### Adicionado

- Estrutura base do projeto: `api/`, `web/`, `nginx/`
- API FastAPI com instância `aplicacao`, CORS configurado e rota `GET /saude`
- `database.py` com `motor`, `FabricaSessao`, `Base` e `obter_sessao()` seguindo convenções PT-BR
- `requirements.txt` com FastAPI 0.115, SQLAlchemy 2, Alembic 1.13, Pydantic 2.9, psycopg2
- Alembic inicializado e `env.py` configurado para ler `DATABASE_URL` do `.env`
- Projeto Angular 19 gerado via `ng new` com roteamento e SCSS
- `nginx.conf` para proxy reverso em staging/prod (`/api/` → porta 8000, `/` → porta 4200)
- Banco de dados `casaleconomia_dev` criado no PostgreSQL 16
- Serviços systemd `casaleconomia-api` e `casaleconomia-web` com start automático no boot
- `.gitignore` cobrindo Python, Node e arquivos de ambiente (`.env`)

[Não lançado]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/joseeduardosm/CasalEconomia/releases/tag/v0.1.0
