# Registro de Mudanças

Todas as mudanças notáveis neste projeto estão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
versionamento segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

---

## [0.7.0] — 10/11/2026

### Adicionado

- **Painel principal** (`GET /painel`) — endpoint agregado que retorna em uma chamada: resumo financeiro do mês, faturas abertas, próximos vencimentos, últimos 8 lançamentos e dados do parceiro
- `schemas/painel.py` — contratos Pydantic: `ResumoPainel`, `FaturaAberta`, `ProximoVencimento`, `LancamentoRecente`, `ParceiroPainel`, `RespostaPainel`
- `services/painel.py` — agrega 5 queries: resumo do mês, faturas, vencimentos, recentes e parceiro
- `routers/painel.py` — `GET /painel?mes=YYYY-MM`; mês padrão é o atual
- `PainelService` Angular — `carregar(mes)`, `aceitarPendente`, `ignorarPendente`
- `PainelComponent` — orquestra todos os widgets e recarrega ao mudar o período via `effect()`
- `ResumoMesComponent` — grade 4×1 com cards clicáveis: Receitas, Despesas, Saldo, A pagar; subvalores e cores por tipo
- `FaturasCardComponent` — lista faturas abertas com barra de progresso e destaque vermelho para vencimentos próximos
- `LancamentosRecentesComponent` — últimos 8 lançamentos com ícone de tipo, valor colorido e link "Ver todos"
- `ProximosVencimentosComponent` — vencidos e próximos 14 dias com destaque urgente/vencido
- `WidgetParceiroComponent` — pendentes inline com aceitar/ignorar sem sair do painel, resumo bilateral
- `DrawerDetalheComponent` — painel lateral deslizante com tabela ordenável, total no rodapé e link para Lançamentos; bottom-sheet no mobile

---

## [0.6.0] — 10/11/2026

### Adicionado

- **Receitas (frontend)** — filtros de tipo Todos/Despesas/Receitas na barra superior de lançamentos
- Chips de status de receita com cores semânticas: `previsto` (azul), `a_receber` (amarelo), `parcialmente_recebido` (laranja), `recebido` (verde)
- FAB expansível na tela de lançamentos — abre submenu com sub-botões "Despesa" e "Receita"
- Botão "Marcar como recebido" (✓) inline para receitas com status previsto ou a_receber
- Modal de criação de receita separado com campos: descrição, data, valor, fonte (select), categoria, nota e flag "Já recebido"
- `criarReceita()` e `marcarRecebido()` no `LancamentosService`
- Valor de receitas exibido em verde na lista de lançamentos; borda lateral verde nos itens tipo receita

---

## [0.5.0] — 10/11/2026

### Adicionado

- **Receitas (backend)** — colunas `fonte` e `valor_recebido` na tabela `lancamentos` (migração `9d562816af83`)
- `calcular_status_receita()` — calcula dinamicamente `previsto`, `a_receber`, `parcialmente_recebido` ou `recebido`
- `enriquecer_lancamento()` — anexa `status_receita` ao objeto ORM antes de serializar
- `FORMAS_INVALIDAS_RECEITA` — rejeita boleto, cartão débito e crédito em receitas
- Validação de receita no `criar_lancamento`: rejeita parcelamento e cartão; `liquidado` padronizado para `False`
- `GET /lancamentos` aceita parâmetro `tipo` para filtrar por `receita` ou `despesa`
- `PUT /lancamentos/{id}` com lógica especial de receita: ao `liquidado=True` registra `valor_recebido` e `data_liquidacao`; ao `liquidado=False` zera ambos
- `RespostaLancamento` ampliado com `fonte`, `valor_recebido` e `status_receita`

---

## [0.4.0] — 10/11/2026

### Adicionado

- **Despesas** — `LancamentosComponent` completo com lista agrupada por data, modal de criação (Seção A/B, "Salvar e continuar"), modal de importação XLSX em 2 etapas e FAB flutuante
- `CartaoService` Angular — `listar`, `criar`, `atualizar`, `arquivar`, `detalheFatura`, `pagarFatura`, `historico`
- `LancamentosService` Angular — `listar`, `criar`, `atualizar`, `excluir`, `baixarModelo`, `validarImportacao`, `confirmarImportacao`
- `FaturaComponent` — detalhe completo de fatura com lançamentos do cartão e formulário de pagamento
- `CartoesComponent` — grade de cartões com formulário de criação inline e status de fatura atual

---

## [0.3.1] — 10/11/2026

### Adicionado

- **Cartões de crédito** — modelo ORM `Cartao` + `Fatura`, migração Alembic `0199ee1a6d31`
- Serviço `cartao.py` com `garantir_faturas` (idempotente), `calcular_periodo_fatura`, `calcular_status_fatura`, `listar_cartoes`, `detalhe_fatura`, `pagar_fatura`
- `roteador_cartao` com 7 rotas: CRUD de cartões, detalhe/pagamento de fatura e histórico
- `SerieParcelamento` — modelo ORM com `total_parcelas` e `parcela_inicio` para rastrear séries
- Lançamentos parcelados com distribuição de centavos via `ROUND_DOWN` e `_distribuir_centavos()`
- Compartilhamento de lançamentos com validação de e-mail do parceiro via `_verificar_parceiro_por_email()`
- `APScheduler 3.10.4` com `BackgroundScheduler` — job de 60s que sincroniza lançamentos com o parceiro e garante faturas futuras
- `openpyxl 3.1.5` + `python-multipart 0.0.9` para importação XLSX

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

[Não lançado]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/joseeduardosm/CasalEconomia/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/joseeduardosm/CasalEconomia/releases/tag/v0.1.0
