# Tarefa 03 — Navegação (Layout, Sidebar e Roteamento)

## Contexto

Implementa a estrutura de navegação do aplicativo: um layout AppShell com sidebar lateral no
desktop e barra de navegação inferior no mobile. Todas as rotas autenticadas ficam dentro do
AppShell. Inclui um seletor de período (mês/ano) na barra superior, pois a maioria das telas
exibe dados financeiros de um período específico.

**Por que sidebar e não topbar:** sidebar preserva espaço vertical (precioso para listas
financeiras) e o espaço horizontal no desktop fica subutilizado. No mobile, a barra inferior
replica o padrão de apps financeiros consolidados.

**Pré-requisito:** tarefa 02 concluída.

---

## Componentes Angular a criar

### `ConchaComponent` — AppShell (layout raiz)
- Wrapper de todas as rotas autenticadas
- Renderiza `NavLateralComponent` + `BarraTopoComponent` + `<router-outlet>`
- No mobile (< 768px): oculta sidebar, exibe `NavMobileComponent` na parte inferior
- Responsável por prover `tituloPagina` e `mesAtivo` (via signal ou serviço) para os filhos

### `NavLateralComponent` — Sidebar
- Largura fixa 220px no desktop
- Logo + nome do app no topo
- Lista de itens de navegação com ícone, rótulo e link ativo destacado
- Link de logout na parte inferior (chama `AuthService.sair()`)
- Itens de menu: array de `{ rotulo, caminho, icone }`

### `BarraTopoComponent` — Barra superior
- Exibe título da página atual
- Seletor de período: botão `<` (mês anterior), label "Nov 2026", botão `>` (mês seguinte)
- Métodos: `irParaMesAnterior()`, `irParaMesSeguinte()`
- O período ativo é exposto como signal compartilhado para outros componentes lerem

### `NavMobileComponent` — Barra inferior (mobile)
- Visível apenas em telas < 768px
- Máximo 5 ícones principais (os mais usados)
- Item ativo destacado com cor CTA

---

## Rotas da aplicação

Todas dentro do `ConchaComponent` (com `authGuard`):

| Rota | Componente | Descrição |
|---|---|---|
| `/painel` | `PainelComponent` | Visão geral financeira do mês |
| `/lancamentos` | `LancamentosComponent` | Lista de lançamentos |
| `/contas` | `ContasComponent` | Contas bancárias |
| `/cartoes` | `CartoesComponent` | Cartões de crédito |
| `/metas` | `MetasComponent` | Metas financeiras |
| `/relatorios` | `RelatoriosComponent` | Relatórios e gráficos |
| `/casal` | `CasalComponent` | Visão compartilhada do casal |
| `/configuracoes` | `ConfiguracoesComponent` | Configurações da conta |

Rotas públicas (fora do AppShell):
- `/login` — `LoginComponent`
- `/cadastro` — `CadastroComponent`
- `/convite/:token` — `ConviteComponent` (tarefa 04)

Rota raiz `/` → redireciona para `/painel`.
Rota não encontrada `**` → redireciona para `/painel`.

Todos os `loadComponent` usam lazy loading.

---

## Itens de menu

| Rótulo | Caminho | Ícone (ng-icons heroicons) |
|---|---|---|
| Painel | `/painel` | `heroHome` |
| Lançamentos | `/lancamentos` | `heroDocumentText` |
| Contas | `/contas` | `heroBuildingLibrary` |
| Cartões | `/cartoes` | `heroCreditCard` |
| Metas | `/metas` | `heroFlag` |
| Relatórios | `/relatorios` | `heroChartBar` |
| Casal | `/casal` | `heroUsers` |
| Configurações | `/configuracoes` | `heroCog6Tooth` |

---

## Componentes de placeholder

Criar componente mínimo (apenas `<h2>`) para cada rota que ainda não tem implementação:
`PainelComponent`, `LancamentosComponent`, `ContasComponent`, `MetasComponent`,
`RelatoriosComponent`, `CasalComponent`, `ConfiguracoesComponent`.

---

## Design

- Sidebar: fundo `#ffffff`, borda direita `#e8e6e5`, item ativo com fundo `rgba(59,166,241,0.08)` e texto `#3ba6f1`
- Barra topo: fundo `#ffffff`, borda inferior `#e8e6e5`, altura 56px
- Mobile bottom: fundo `#ffffff`, borda superior `#e8e6e5`
- Tokens CSS em `:root`: `--color-primary`, `--color-secondary`, `--color-ash`, `--color-canvas`, `--color-card`, `--color-border`, `--color-cyan`, `--color-cyan-edge`, `--radius-button`, `--radius-input`
- Dark mode via `@media (prefers-color-scheme: dark)` e `[data-theme="dark"]`

---

## Verificação

- Acessar `http://localhost:4200` → redireciona para `/painel` (com login)
- Sidebar aparece no desktop; some no mobile (< 768px)
- Barra inferior aparece no mobile
- Clicar em cada item do menu → URL muda e item fica ativo
- Período avança/recua corretamente ao clicar nas setas
- Reload em qualquer rota protegida → permanece na rota (não redireciona)

---

## Fora do escopo

- Conteúdo real das telas (implementado em tarefas específicas)
- Preferência de tema persistida
