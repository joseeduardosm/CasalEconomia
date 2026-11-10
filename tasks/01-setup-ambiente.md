# Tarefa 01 — Setup do Ambiente e Estrutura Base

## Contexto

Preparar o ambiente de desenvolvimento local para o CasalEconomia. Ao final desta tarefa a API
FastAPI responde em `http://localhost:8000/saude` e o Angular serve em `http://localhost:4200`.

**Stack:** Angular 19, FastAPI (Python 3.12), PostgreSQL 16, NGINX 1.26 (só prod), Alembic, SQLAlchemy 2.

---

## Estrutura de pastas a criar

```
casaleconomia/
├── api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── domain/
│   │   ├── schemas/
│   │   └── models/
│   ├── alembic/
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
├── nginx/
│   └── nginx.conf
└── web/               ← criado via `ng new`
```

---

## Dependências Python (`requirements.txt`)

| Pacote | Versão |
|---|---|
| fastapi | 0.115.0 |
| uvicorn[standard] | 0.30.6 |
| sqlalchemy | 2.0.35 |
| alembic | 1.13.3 |
| pydantic | 2.9.2 |
| pydantic-settings | 2.5.2 |
| psycopg2-binary | 2.9.9 |
| python-dotenv | 1.0.1 |

---

## Variáveis de ambiente (`.env.example`)

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | String de conexão PostgreSQL | `postgresql://postgres:postgres@localhost:5432/casaleconomia_dev` |
| `SECRET_KEY` | Chave para assinar tokens JWT | qualquer string longa aleatória |
| `CORS_ORIGINS` | Origens permitidas no CORS | `http://localhost:4200` |

---

## Responsabilidades de cada arquivo

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Instância FastAPI, CORS, inclusão de routers. Variável da app: `aplicacao` |
| `database.py` | Engine (`motor`), session factory (`FabricaSessao`), `Base`, gerador `obter_sessao()` |
| `models/__init__.py` | Importa todos os modelos para o Alembic detectar |

**Convenções obrigatórias em todo o projeto:**
- Nome da instância FastAPI: `aplicacao` (não `app`)
- Nome do `create_engine`: `motor`
- Nome do `sessionmaker`: `FabricaSessao`
- Nome de todo `APIRouter`: `roteador`
- Nomes de variáveis, funções, campos: **PT-BR** em snake_case
- Todo arquivo começa com uma docstring de parágrafo explicando o que é e por que existe
- Código amplamente comentado em PT-BR

---

## CORS

Configurar com `allow_origins=origens_permitidas`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`. `origens_permitidas` lida de `CORS_ORIGINS` do `.env`.

---

## Rota de saúde

`GET /saude` — sem autenticação — retorna `{"status": "ok"}`.

---

## NGINX (`nginx/nginx.conf`)

Proxy reverso: `/api/` → `localhost:8000`, todo o resto → `localhost:4200`. Usado em staging/prod; em dev não é necessário.

---

## Banco de dados

Criar banco local antes de iniciar:
```
psql -U postgres -c "CREATE DATABASE casaleconomia_dev;"
```

Inicializar Alembic dentro de `api/`:
```
alembic init alembic
```

Configurar `alembic.ini` para usar `DATABASE_URL` do `.env` e `alembic/env.py` para importar o `Base` e os modelos.

---

## Como rodar em desenvolvimento

**Terminal 1 — API:**
```
cd api && source .venv/bin/activate
uvicorn app.main:aplicacao --reload --port 8000
```

**Terminal 2 — Web:**
```
cd web && ng serve
```

---

## Verificação

- `curl http://localhost:8000/saude` → `{"status":"ok"}`
- `curl http://localhost:8000/docs` → documentação OpenAPI renderiza
- `http://localhost:4200` → tela padrão do Angular carrega sem erro no console

---

## Fora do escopo

- Autenticação
- Qualquer rota além de `/saude`
- Configuração de CI/CD
