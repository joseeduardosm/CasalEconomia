# Tarefa 12 — Relatórios

## Contexto

Implementa a tela `/relatorios` com cinco relatórios financeiros, inspirados diretamente nas
páginas de relatórios do OpenMonetis (`/reports/financial-distribution`, `/reports/category-trends`,
`/reports/commitments`, `/reports/installments`, `/reports/recurring-transactions`).

Cada relatório é uma aba separada. Todos têm filtros de período e os dados são calculados no
backend — o frontend não realiza nenhum cálculo financeiro.

**Pré-requisito:** tarefas 01–11 concluídas.

---

## Relatórios a implementar

### R1 — Distribuição Financeira (`/reports/financial-distribution`)

**O que é:** quanto do dinheiro foi para onde, no período. Visão de despesas agrupadas por
categoria, forma de pagamento e tipo (cartão vs débito vs dinheiro).

**Filtros:** mês/período (`mes_inicio` + `mes_fim`), escopo de pessoa (`proprio` / `parceiro` / `ambos`)

**Dados retornados:**
- Total de receitas, total de despesas, saldo
- Despesas por categoria (nome, valor, % do total)
- Despesas por forma de pagamento (nome, valor, %)
- Receitas por categoria (nome, valor, %)
- Top 5 maiores lançamentos do período

**Visualização:** barras horizontais proporcionais por grupo + tabela detalhada por categoria
(com `TabelaLancamentosComponent` ao clicar em cada linha)

---

### R2 — Tendência de Categorias (`/reports/category-trends`)

**O que é:** como os gastos em cada categoria evoluem mês a mês nos últimos N meses.

**Filtros:** `meses` (3, 6, 12 — default 6), categoria opcional

**Dados retornados:**
- Para cada categoria: array de `{ mes: "2026-10", valor: NUMERIC }` dos últimos N meses
- Média mensal por categoria
- Categorias ordenadas por valor total decrescente

**Visualização:** gráfico de linhas com múltiplas séries (uma por categoria) OU tabela com
meses nas colunas e categorias nas linhas. Toggle entre os dois modos.

---

### R3 — Compromissos (`/reports/commitments`)

**O que é:** quanto de dinheiro já está "comprometido" nos próximos meses — parcelas em aberto
e recorrências ativas que vão gerar despesas futuras.

**Filtros:** `meses_futuros` (1, 3, 6 — default 3)

**Dados retornados:**
Para cada mês futuro:
```
{
  "mes": "2026-12",
  "parcelas_total": NUMERIC,     // soma de parcelas futuras da tabela lancamentos
  "parcelas_count": int,
  "recorrencias_total": NUMERIC, // estimativa baseada nas regras de recorrência (tarefa 10 futura)
  "recorrencias_count": int,
  "total_comprometido": NUMERIC
}
```
- Detalhamento por série: nome da despesa parcelada, valor/parcela, parcelas restantes

**Visualização:** cards por mês com barra de total comprometido + lista das séries de parcelamento

---

### R4 — Parcelas Ativas (`/reports/installments`)

**O que é:** todas as séries de parcelamento em andamento: quanto já foi pago, quanto falta,
em quantas parcelas.

**Filtros:** nenhum (sempre o estado atual — independente de mês)

**Dados retornados:**
Para cada `series_parcelamento` ativa (com parcelas futuras):
```
{
  "serie_id": UUID,
  "descricao": str,              // descrição da primeira parcela
  "cartao_nome": str | null,
  "valor_total": NUMERIC,
  "parcelas_total": int,
  "parcelas_pagas": int,
  "parcelas_restantes": int,
  "valor_pago": NUMERIC,
  "valor_restante": NUMERIC,
  "proxima_parcela_data": DATE,
  "proxima_parcela_valor": NUMERIC
}
```

**Visualização:** lista de cards por série com barra de progresso (% pago) e tabela detalhada
ao clicar. Ordenação: por valor restante decrescente (default).

---

### R5 — Lançamentos Recorrentes (`/reports/recurring-transactions`)

**O que é:** lista de todas as regras de recorrência ativas, com filtros por tipo, status e
forma de pagamento. (Recorrências são implementadas na tarefa 10; este relatório lista o que
está cadastrado.)

**Nota:** se recorrências não estiverem implementadas ao chegar nesta tarefa, criar a tela com
estado vazio adequado e um aviso "Disponível após implementar lançamentos recorrentes".

**Filtros:** `tipo` (receita/despesa/todos), `status` (ativa/pausada/cancelada), `forma_pagamento`,
busca textual `q`

**Dados retornados:**
```
{
  "id": UUID,
  "descricao": str,
  "valor": NUMERIC,
  "tipo": str,
  "forma_pagamento": str,
  "frequencia": str,
  "data_inicio": DATE,
  "data_fim": DATE | null,
  "status": str,
  "total_gerado_no_ano": NUMERIC  // soma de ocorrências liquidadas no ano corrente
}
```

**Visualização:** `TabelaLancamentosComponent` adaptada (colunas: Descrição, Valor, Frequência,
Status, Início, Total ano) com busca e ordenação.

---

## Endpoints novos (todos autenticados)

| Endpoint | Query params | Descrição |
|---|---|---|
| `GET /relatorios/distribuicao` | `mes_inicio`, `mes_fim`, `escopo` | Relatório R1 |
| `GET /relatorios/tendencia-categorias` | `meses` (3/6/12) | Relatório R2 |
| `GET /relatorios/compromissos` | `meses_futuros` (1/3/6) | Relatório R3 |
| `GET /relatorios/parcelas-ativas` | — | Relatório R4 |
| `GET /relatorios/recorrentes` | `tipo`, `status`, `forma_pagamento`, `q` | Relatório R5 |

Todos filtram por `usuario_id` autenticado.

## Novos arquivos backend

| Arquivo | Ação |
|---|---|
| `api/app/schemas/relatorios.py` | Criar — schemas de output de cada relatório |
| `api/app/services/relatorios.py` | Criar — queries agregadas para cada relatório |
| `api/app/routers/relatorios.py` | Criar — 5 endpoints |
| `api/app/main.py` | Atualizar — incluir router |

---

## Frontend

### Tela `/relatorios` (substituir placeholder)

- Abas no topo: **Distribuição · Tendências · Compromissos · Parcelas · Recorrentes**
- Cada aba lazy-carrega seu conteúdo apenas quando selecionada
- Filtros específicos por aba ficam abaixo das abas, acima do conteúdo
- Período padrão: mês atual (herdado do `BarraTopoComponent`) exceto R4 e R5

### Visualizações

- **Barras horizontais** (R1, R3): elementos `<div>` com largura proporcional em CSS —
  sem biblioteca de gráficos; apenas HTML + tokens de cor
- **Gráfico de linhas** (R2): usar `Chart.js` via `chart.js@4.4.3` (npm) com canvas.
  Paleta de cores: até 8 categorias com cores distintas definidas em `icones-pagamento.ts`
  (expandir o arquivo com `CORES_CATEGORIAS`)
- **Cards de progresso** (R4): barra de progresso CSS com `valor_pago / valor_total * 100%`
- **Tabela** (R5): `TabelaLancamentosComponent` com colunas adaptadas
- Todos os elementos de barra/card são clicáveis e abrem `DrawerDetalheComponent` com os
  lançamentos que compõem aquele dado

### `RelatoriosService` (Angular, singleton)

Métodos: `distribuicao(params)`, `tendenciaCategorias(params)`, `compromissos(params)`,
`parcelasAtivas()`, `recorrentes(params)`

---

## Verificação

```bash
# 1. Distribuição do mês
curl -s "http://localhost:8000/relatorios/distribuicao?mes_inicio=2026-11&mes_fim=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: total_receitas, total_despesas, saldo, por_categoria, por_forma_pagamento

# 2. Tendência (últimos 3 meses)
curl -s "http://localhost:8000/relatorios/tendencia-categorias?meses=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: array por categoria com valores mensais

# 3. Compromissos dos próximos 3 meses
curl -s "http://localhost:8000/relatorios/compromissos?meses_futuros=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: array por mês com parcelas e total comprometido

# 4. Parcelas ativas
curl -s http://localhost:8000/relatorios/parcelas-ativas \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lista de séries com valor_pago, valor_restante, proxima_parcela_data

# 5. Recorrentes (somente despesas ativas)
curl -s "http://localhost:8000/relatorios/recorrentes?tipo=despesa&status=ativa" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lista de regras recorrentes
```

Frontend:
- Abrir `/relatorios` → aba "Distribuição" ativa por padrão
- Trocar mês no seletor → relatório recarrega com o novo período
- Aba "Parcelas" → cards com barra de progresso para cada série de parcelamento
- Clicar em barra de categoria → `DrawerDetalheComponent` abre com lançamentos daquela categoria
- Aba "Recorrentes" → tabela com busca e colunas ordenáveis

---

## Fora do escopo

- Exportação PDF / XLSX
- Relatórios de orçamento vs realizado (metas — tarefa 14)
- Comparativo casal (tarefa 13)
- Projeção de fluxo de caixa futuro além de parcelas
- Relatórios customizáveis pelo usuário
