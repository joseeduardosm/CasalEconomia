# Registro de Mudanças

Todas as mudanças notáveis neste projeto estão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

---

## [0.3.0] — 10/11/2026

### Adicionado

- `ConchaComponent` (AppShell) — layout raiz para todas as rotas autenticadas: sidebar + barra superior + router-outlet + navegação mobile
- `NavLateralComponent` — sidebar fixa de 220px com 8 itens de menu, item ativo destacado em ciano (`rgba(59,166,241,0.08)`), botão de logout no rodapé
- `BarraTopoComponent` — barra superior de 56px com título da rota ativa e seletor de período (mês/ano)
- `NavMobileComponent` — barra inferior fixa para telas < 768px com os 5 módulos principais
- `PeriodoService` — signal Angular com `mesAtivo`, `labelPeriodo` e métodos `irParaMesAnterior` / `irParaMesSeguinte`
- 7 componentes placeholder com carregamento tardio: `LancamentosComponent`, `ContasComponent`, `CartoesComponent`, `MetasComponent`, `RelatoriosComponent`, `CasalComponent`, `ConfiguracoesComponent`
- Rotas autenticadas aninhadas sob `ConchaComponent` com `authGuard` no pai; `loadComponent` lazy em todos os filhos
- Ícones Heroicons via `@ng-icons/core@29.10.0` + `@ng-icons/heroicons@29.10.0` (compatíveis com Angular 19)
- `provideIcons` registrado em `app.config.ts` com todos os ícones usados
- Convenção de cabeçalho `pq existe / para que no projeto` aplicada em todos os arquivos existentes

### Alterado

- `PainelComponent` — removido botão de logout (agora na sidebar); template simplificado para placeholder
- `app.routes.ts` — rotas autenticadas migradas para filhas de `ConchaComponent`; rotas públicas permanecem soltas
- Cabeçalhos de todos os arquivos do projeto atualizados com a seção `pq existe / para que no projeto`
- Comentários do projeto convertidos para PT-BR puro (sem termos técnicos em inglês onde há equivalente)

---

## [0.2.0] — 10/11/2026

### Adicionado

- Autenticação completa com JWT (HS256, expiração de 7 dias)
- Tabela `users` com UUID, nome, e-mail único e senha em hash bcrypt — criada via migração Alembic
- Endpoints `POST /auth/registrar` (201) e `POST /auth/entrar` (200)
- Repositório `usuario.py` com `buscar_por_email` e `criar`
- Schemas Pydantic: `EntradaCadastro`, `EntradaLogin`, `RespostaToken`
- Serviço `auth.py` com `gerar_token`, `verificar_token`, `gerar_hash_senha` e `verificar_senha`
- Função `_obter_usuario_atual` para extração do usuário via cabeçalho `Authorization: Bearer`
- `AuthService` Angular singleton com `salvarToken`, `getToken`, `estaAutenticado` e `sair`
- `authInterceptor` funcional — injeta o token JWT em todas as requisições autenticadas
- `authGuard` funcional — redireciona para `/login` se não autenticado
- Telas de login e cadastro com design Seline Analytics (card centralizado, max 440px, CTA azul)
- Rota `/painel` placeholder protegida por `authGuard`
- Variáveis de ambiente Angular em `src/environments/`

### Corrigido

- Downgrade de `bcrypt` para `4.0.1` para manter compatibilidade com `passlib 1.7.4`
- Adicionado `pydantic[email]` ao `requirements.txt` para suporte a `EmailStr`

---

## [0.1.0] — 10/11/2026

### Adicionado

- Estrutura base do projeto: `api/`, `web/`, `nginx/`
- API FastAPI com instância `aplicacao`, CORS configurado e rota `GET /saude`
- `database.py` com `motor`, `FabricaSessao`, `Base` e `obter_sessao()` seguindo convenções PT-BR
- `requirements.txt` com FastAPI 0.115, SQLAlchemy 2, Alembic 1.13, Pydantic 2.9, psycopg2
- Alembic inicializado e `env.py` configurado para ler `DATABASE_URL` do `.env`
- Projeto Angular 19 gerado via `ng new` com roteamento e SCSS
- `nginx.conf` para proxy reverso em staging/prod (`/api/` → porta 8000, `/` → porta 4200)
- Banco de dados `casaleconomia_dev` criado no PostgreSQL 16
- Serviços systemd `casaleconomia-api` e `casaleconomia-web` com inicialização automática no boot
- `.gitignore` cobrindo Python, Node e arquivos de ambiente (`.env`)

[Não lançado]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/joseeduardosm/CasalEconomia/releases/tag/v0.1.0
