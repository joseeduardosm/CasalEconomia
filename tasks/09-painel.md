# Tarefa 09 — Painel Principal (Dashboard)

## Contexto

Implementa a tela `/painel`, criada como placeholder na tarefa 03. É a tela inicial do app —
o usuário chega aqui depois do login. Exibe um panorama financeiro do mês ativo (período herdado
do `BarraTopoComponent`), organizado em widgets: resumo financeiro, faturas de cartão, próximos
vencimentos, lançamentos recentes e, quando há parceiro conectado, um widget de visão do casal
com aceite de lançamentos inline.

Toda a data vem de um único endpoint agregado `GET /painel?mes=YYYY-MM` — uma chamada, sem
cascata de requests no carregamento.

**Pré-requisito:** tarefas 01–08 concluídas.

---

## Melhorias sobre o OpenMonetis

| # | Problema original | Decisão aqui |
|---|---|---|
| 1 | Dashboard mostra somente finanças individuais | Widget "Visão do Casal" com despesas/receitas de cada pessoa lado a lado |
| 2 | Alertas de vencimento sepultados na lista de lançamentos | Destaque visual para faturas e lançamentos vencendo em ≤ 5 dias diretamente no painel |
| 3 | Aceitar lançamentos do parceiro exige navegar para outra tela | Widget Parceiro inline — aceitar/ignorar sem sair do painel |
| 4 | Sem distinção entre receita esperada e recebida nos totais | Card Receitas mostra "Recebido R$ X" + "A receber R$ Y" como subvalores |
| 5 | Carregamento serial de múltiplos endpoints | Um endpoint `GET /painel` agrega tudo; frontend faz 1 request por troca de período |
| 6 | Widgets são estáticos — clicar não faz nada | Todos os cards e widgets são clicáveis e abrem um drawer/modal com tabela detalhada ordenável |

---

## Novos arquivos backend

| Arquivo | Ação |
|---|---|
| `api/app/schemas/painel.py` | Criar — schemas Pydantic de output |
| `api/app/services/painel.py` | Criar — agrega dados de lançamentos, faturas e parceiro |
| `api/app/routers/painel.py` | Criar — `GET /painel` |
| `api/app/main.py` | Atualizar — incluir router de painel |

O service faz 4 queries independentes (resumo, faturas, próximos vencimentos, lançamentos
recentes) mais 1 condicional para dados do parceiro. Não há lógica de negócio nova; reutiliza os
repositories de `lancamentos` e `faturas` existentes.

---

## Endpoint `GET /painel`

**Autenticação:** obrigatória  
**Query param:** `mes` (YYYY-MM, default mês atual)  
**Response 200:**

### `resumo_mes`

| Campo | Tipo | Descrição |
|---|---|---|
| `total_receitas` | NUMERIC | Soma de receitas do mês |
| `total_receitas_recebidas` | NUMERIC | Soma de receitas com `liquidado = true` |
| `total_despesas` | NUMERIC | Soma de despesas do mês |
| `total_despesas_pagas` | NUMERIC | Soma de despesas com `liquidado = true` (exceto cartão) |
| `saldo` | NUMERIC | `total_receitas − total_despesas` |
| `a_receber` | NUMERIC | Receitas com `liquidado = false` |
| `a_pagar` | NUMERIC | Despesas com `liquidado = false` |

### `faturas_abertas` (array)

| Campo | Tipo | Descrição |
|---|---|---|
| `fatura_id` | UUID | |
| `cartao_nome` | str | |
| `cartao_cor` | str | Hex, ex: `"#8a05be"` |
| `valor_total` | NUMERIC | |
| `valor_pago` | NUMERIC | |
| `valor_restante` | NUMERIC | |
| `data_vencimento` | DATE | |
| `status` | str | `aberta/fechada/parcialmente_paga/paga/vencida` |
| `vencendo_em_breve` | bool | `true` se `data_vencimento <= hoje + 5 dias` |

Incluir faturas com `periodo = mes` informado e `status != "paga"`.

### `proximos_vencimentos` (array)

Lançamentos com `data_vencimento` entre hoje e hoje + 14 dias (inclusive vencidos com
`liquidado = false`), ordenados por `data_vencimento` ASC.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | |
| `descricao` | str | |
| `valor` | NUMERIC | |
| `data_vencimento` | DATE | |
| `tipo` | str | `receita` ou `despesa` |
| `liquidado` | bool | |
| `dias_para_vencer` | int | Negativo se vencido |
| `vencido` | bool | `data_vencimento < hoje AND liquidado = false` |

### `lancamentos_recentes` (array, máx 8)

Últimos 8 lançamentos do mês, ordenados por `data_lancamento DESC`.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | |
| `descricao` | str | |
| `valor` | NUMERIC | |
| `tipo` | str | |
| `data_lancamento` | DATE | |
| `forma_pagamento` | str, nullable | |
| `liquidado` | bool, nullable | |
| `parcela_atual` | int, nullable | |
| `total_parcelas` | int, nullable | |
| `cartao_nome` | str, nullable | |

### `parceiro` (objeto ou `null`)

`null` se o usuário não tem parceiro conectado.

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | str | Nome do parceiro |
| `pendentes_count` | int | Total de `lancamentos_parceiro` com `status = "pendente"` |
| `pendentes` | array (máx 3) | Preview inline dos primeiros 3 pendentes |
| `pendentes[].id` | UUID | ID do `lancamentos_parceiro` |
| `pendentes[].snapshot_descricao` | str | |
| `pendentes[].snapshot_valor` | NUMERIC | |
| `pendentes[].snapshot_data` | DATE | |
| `pendentes[].snapshot_tipo` | str | |
| `resumo_despesas` | NUMERIC | Total de despesas do parceiro no mês |
| `resumo_receitas` | NUMERIC | Total de receitas do parceiro no mês |

---

## Regras de negócio

- `resumo_mes.total_despesas_pagas` conta apenas despesas sem `cartao_id` (cartão é controlado pela fatura)
- `a_pagar` = soma de despesas com `liquidado = false` (cartão com `liquidado = null` não entra)
- O resumo do parceiro (`resumo_despesas`, `resumo_receitas`) busca `lancamentos` onde
  `usuario_id = id_parceiro` — somente os lançamentos próprios do parceiro, não os compartilhados
- `vencendo_em_breve` em fatura: comparar `data_vencimento` da fatura com `date.today() + 5 dias`
- Lançamentos vencidos em `proximos_vencimentos`: incluir itens com `data_vencimento < hoje`
  e `liquidado = false` (janela estendida: sem limite de dias para o passado, apenas 14 dias para
  o futuro)

---

## Frontend

### Layout da tela `/painel`

**Desktop (≥ 768px):**
```
┌──────────────────────────────────────────────────────────────┐
│  [Receitas]    [Despesas]    [Saldo]    [A pagar]            │  ← 4 cards (largura total)
├──────────────────────────────────┬───────────────────────────┤
│  Lançamentos recentes  (2/3)     │  Faturas de cartão  (1/3) │
├──────────────────────────────────┼───────────────────────────┤
│  Próximos vencimentos  (2/3)     │  Parceiro (1/3, se ativo) │
└──────────────────────────────────┴───────────────────────────┘
```

**Mobile (< 768px) — coluna única, ordem de prioridade:**
1. Resumo do mês (grade 2×2)
2. Widget Parceiro (somente se houver pendentes)
3. Lançamentos recentes
4. Próximos vencimentos
5. Faturas de cartão

### Interatividade geral dos widgets

**Todos os cards de resumo e todos os widgets são clicáveis.** Ao clicar em qualquer elemento
(card de total, linha de fatura, linha de lançamento, linha de vencimento), abre um
`DrawerDetalheComponent` — painel lateral deslizante (desktop) ou modal bottom-sheet (mobile) —
exibindo uma **tabela detalhada** com os lançamentos que compõem aquele dado.

#### `DrawerDetalheComponent`

- Título dinâmico (ex: "Receitas de novembro", "Lançamentos desta fatura")
- Tabela com colunas ordenáveis (clique no cabeçalho alterna ASC/DESC):
  - Descrição, Data, Valor, Forma de pagamento, Status, Categoria
  - Colunas exibidas variam por contexto (ex: fatura omite "Forma de pagamento")
- Ordenação padrão: `data DESC`
- Rodapé com total dos valores exibidos
- Botão "Ver todos em Lançamentos" → navega para `/lancamentos` com filtros pré-aplicados
- Fecha ao clicar fora (overlay) ou no botão "×"

#### Mapeamento clique → drawer

| Elemento clicado | Título do drawer | Lançamentos exibidos |
|---|---|---|
| Card "Receitas" | "Receitas de [mês]" | `tipo=receita` do mês |
| Card "Despesas" | "Despesas de [mês]" | `tipo=despesa` do mês |
| Card "Saldo" | "Lançamentos de [mês]" | todos do mês |
| Card "A pagar" | "A pagar em [mês]" | `tipo=despesa, liquidado=false` |
| Fatura de cartão | "Lançamentos — [nome cartão] [período]" | lançamentos da fatura |
| Lançamento recente (linha) | "Detalhe do lançamento" | modal de detalhe único |
| Widget "Próximos vencimentos" (linha) | "Detalhe do lançamento" | modal de detalhe único |
| Widget Parceiro — "Suas despesas" | "Suas despesas de [mês]" | despesas do usuário |
| Widget Parceiro — "Despesas de [Nome]" | "Despesas de [Nome] em [mês]" | despesas do parceiro |

O `DrawerDetalheComponent` recebe um `filtro` como Input e chama `GET /lancamentos` com esses
parâmetros — reutiliza o endpoint existente da tarefa 07, sem endpoint novo.

### Widget Resumo do mês (4 cards)

| Card | Valor principal | Subvalor | Cursor |
|---|---|---|---|
| Receitas | `total_receitas` | "Recebido R$ X" / "A receber R$ Y" | pointer (clicável) |
| Despesas | `total_despesas` | "Pago R$ X / Pendente R$ Y" | pointer (clicável) |
| Saldo | `saldo` | verde se positivo, vermelho se negativo | pointer (clicável) |
| A pagar | `a_pagar` | "em X lançamentos" | pointer (clicável) |

Tokens de cor: receitas = `#22c55e`, despesas = `#ef4444`, saldo = dinâmico, a pagar = `#f59e0b`

### Widget Faturas de cartão

- Título "Faturas do mês"
- Para cada fatura: faixa colorida lateral com `cartao_cor`, nome do cartão, valor restante em
  destaque, data de vencimento
- `vencendo_em_breve = true` → fundo `rgba(239,68,68,0.06)` + ícone de alerta vermelho
- **Clicar em qualquer fatura** → abre drawer com lançamentos daquela fatura
- Botão "Ver fatura completa" → navega para `/cartoes/:id/fatura?fatura_id=X`
- Estado vazio: "Nenhuma fatura aberta este mês"

### Widget Lançamentos recentes

- Título "Últimos lançamentos" + link "Ver todos" → `/lancamentos?mes=YYYY-MM`
- Até 8 itens: ícone ↑ (receita) / ↓ (despesa), descrição, valor colorido, data, chip de
  forma de pagamento
- Parcela exibida como "(2/6)" quando `parcela_atual` preenchido
- **Clicar em qualquer item** → abre drawer com detalhe do lançamento (data, valor, nota,
  parcelas da série se parcelado, compartilhamento se aplicável)

### Widget Próximos vencimentos

- Título "Próximos vencimentos"
- `vencido = true` → fundo vermelho suave + rótulo "Vencido"
- `dias_para_vencer <= 5 AND !vencido` → fundo amarelo suave + rótulo "Vence em N dias"
- Outros: listagem comum com data
- Estado vazio: "Nenhum vencimento nos próximos 14 dias"
- **Clicar em qualquer item** → abre drawer com detalhe do lançamento

### Widget Parceiro

**Sem pendentes:** resumo bilateral
- Nome do parceiro no topo
- "Suas despesas: R$ X" / "Despesas de [Nome]: R$ Y"
- Barra proporcional visual (proporção entre os dois valores)

**Com pendentes:** seção de pendentes em destaque
- Título "Lançamentos de [Nome] para você" + badge `pendentes_count`
- Até 3 itens: descrição, valor, tipo, data
- Botões "Aceitar" / "Ignorar" inline por item → chamam respectivamente
  `POST /parceiro/{id}/aceitar` (com `versao_esperada = 0`) e `POST /parceiro/{id}/ignorar`
  (endpoints já existem da tarefa 05)
- Se `pendentes_count > 3`: link "Ver todos os X pendentes" → `/lancamentos?pendentes=true`
- Abaixo dos pendentes: mesmo resumo bilateral descrito acima

### `PainelService` (Angular, singleton)

- `carregarPainel(mes: string)` → `GET /painel?mes=X`
- Reutiliza `aceitarPendente(id)` e `ignorarPendente(id)` do serviço existente da tarefa 05
  (ou delega a um `SincronizadorService` se já isolado)

### Componentes a criar

```
web/src/app/features/painel/
  painel.component.ts / .html / .scss
  components/
    resumo-mes.component.ts / .html / .scss
    faturas-card.component.ts / .html / .scss
    lancamentos-recentes.component.ts / .html / .scss
    proximos-vencimentos.component.ts / .html / .scss
    widget-parceiro.component.ts / .html / .scss
web/src/app/shared/components/
  drawer-detalhe/
    drawer-detalhe.component.ts / .html / .scss   ← reutilizável em outras telas
web/src/app/core/services/painel.service.ts
```

O `PainelComponent` recebe o mês do `BarraTopoComponent` via signal (definido na tarefa 03) e
recarrega o painel ao detectar mudança de período.

---

## Verificação

```bash
# 1. Painel básico (sem parceiro, sem dados)
curl -s "http://localhost:8000/painel?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: resumo_mes com zeros, faturas_abertas=[], proximos_vencimentos=[],
#           lancamentos_recentes=[], parceiro=null

# 2. Totais corretos após criar lançamentos
# receita liquidada R$5000 + despesa liquidada R$2000 + despesa pendente R$500
curl -s "http://localhost:8000/painel?mes=2026-11" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['resumo_mes']; print(r)"
# esperado: total_receitas=5000, total_despesas=2500, saldo=2500, a_pagar=500,
#           total_receitas_recebidas=5000, total_despesas_pagas=2000

# 3. Alerta de vencimento próximo
# criar lançamento com data_vencimento = hoje + 3 dias, liquidado=false
curl -s "http://localhost:8000/painel?mes=2026-11" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; v=json.load(sys.stdin)['proximos_vencimentos']; print(v)"
# esperado: item com vencendo_em_breve=true (ou vencido=false, dias_para_vencer<=5)

# 4. Fatura vencendo em breve
# criar cartão + fatura com data_vencimento = hoje + 2 dias
curl -s "http://localhost:8000/painel?mes=2026-11" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; f=json.load(sys.stdin)['faturas_abertas']; print(f)"
# esperado: fatura com vencendo_em_breve=true

# 5. Widget parceiro com pendentes
# conectar dois usuários; parceiro A cria lançamento; verificar no painel do usuário B
curl -s "http://localhost:8000/painel?mes=2026-11" -H "Authorization: Bearer $TOKEN_B" \
  | python3 -m json.tool
# esperado: parceiro.pendentes_count=1, parceiro.pendentes com 1 item

# 6. Aceitar pendente e verificar que some do painel
curl -s -X POST http://localhost:8000/parceiro/$PENDENTE_ID/aceitar \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json" \
  -d '{"versao_esperada":0}' | python3 -m json.tool
# esperado: aceito; próximo GET /painel mostra pendentes_count=0

# 7. Trocar mês → dados corretos do outro período
curl -s "http://localhost:8000/painel?mes=2026-10" -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
# esperado: dados do mês de outubro (distintos de novembro)
```

Frontend:
- Abrir `/painel` → 4 widgets renderizados com dados reais
- Avançar mês no seletor (`BarraTopoComponent`) → painel recarrega com dados do novo mês
- Clicar "Aceitar" num pendente do parceiro → item some do widget sem navegação
- Fatura vencendo em breve → destaque vermelho visível no widget de faturas
- Clicar no card "Receitas" → drawer desliza com tabela de receitas do mês; total no rodapé
- Clicar no cabeçalho "Valor" da tabela → ordena ASC; clicar de novo → DESC
- Clicar no card "Despesas" → drawer exibe despesas do mês
- Clicar no card "A pagar" → drawer exibe apenas despesas pendentes
- Clicar em fatura no widget → drawer com lançamentos daquela fatura
- Clicar em item de "Lançamentos recentes" → drawer com detalhe: data, valor, nota, parcelas, compartilhamento
- Clicar em item de "Próximos vencimentos" → mesmo detalhe
- Clicar no overlay do drawer → fecha sem navegar

---

## Fora do escopo

- Gráficos e relatórios visuais (tarefa futura — relatórios)
- Metas financeiras (tarefa futura)
- Saldo de contas bancárias (tarefa futura — contas)
- Notificações push/e-mail de vencimento
- Configuração de quais widgets exibir (personalização)
- Comparativo histórico mês a mês
