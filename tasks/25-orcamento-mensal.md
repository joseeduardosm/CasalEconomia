# Tarefa 25 — Orçamento Mensal por Categoria

## Contexto

Implementa o controle de orçamento do tipo "envelope": o usuário define quanto pretende gastar
em cada categoria por mês, e o sistema acompanha o consumo em tempo real conforme os lançamentos
são registrados. O orçamento é uma **configuração persistente** — definido uma vez, se aplica
automaticamente a todos os meses futuros até ser editado ou desativado, sem necessidade de
recriar a cada período.

Diferença em relação às metas de `limite_gasto` (tarefa 14):

| Orçamento mensal | Meta de limite_gasto (T14) |
|---|---|
| Configuração persistente, sem data de fim | Período explícito (data_inicio / data_fim) |
| Resetado automaticamente todo mês | Calculado exatamente pelo período configurado |
| Foco operacional (gestão do dia a dia) | Foco de objetivo (ex: "em novembro gastar menos") |
| Sem compartilhamento (individual) | Pode ser compartilhada com o parceiro |
| Widget sempre visível no painel | Aparece na seção de metas |

Os dois mecanismos coexistem. O usuário pode usar ambos ou apenas um.

**Pré-requisito:** tarefas 01–24 concluídas. Requer tarefas 15 (contas), 17 (categorias).

---

## Nova tabela

### `orcamentos`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `categoria_id` | UUID FK → `categorias.id` | sim | um orçamento por categoria (unique por usuario_id + categoria_id) |
| `valor_limite` | NUMERIC(12,2) | sim | limite mensal (> 0) |
| `ativo` | BOOLEAN | sim | default `true`; quando `false`, não aparece no painel nem nos cálculos |
| `criado_em` | TIMESTAMPTZ | sim | |
| `atualizado_em` | TIMESTAMPTZ | sim | |

**Restrição única:** `(usuario_id, categoria_id)` — somente um orçamento por categoria por usuário.

---

## Regras de negócio

### Cálculo de consumo mensal

O consumo de um orçamento no mês consultado é calculado dinamicamente a partir dos lançamentos:

```
valor_gasto = SUM(lancamentos.valor)
  WHERE tipo = "despesa"
  AND categoria_id = orcamento.categoria_id
  AND usuario_id = orcamento.usuario_id
  AND data_lancamento ENTRE inicio_mes E fim_mes
  AND transferencia_id IS NULL   -- excluir transferências
```

Lançamentos não liquidados (`liquidado = false`) **entram** no cálculo — o usuário deve saber
o que está comprometido, não apenas o que já saiu da conta.

### Status derivado (não persistido)

| Condição | Status | Cor sugerida |
|---|---|---|
| `valor_gasto / valor_limite < 0.70` | `tranquilo` | verde |
| `0.70 ≤ valor_gasto / valor_limite < 0.90` | `atencao` | amarelo |
| `0.90 ≤ valor_gasto / valor_limite < 1.00` | `critico` | laranja |
| `valor_gasto / valor_limite ≥ 1.00` | `estourado` | vermelho |

### Período consultado

Por padrão, o mês corrente. O endpoint aceita `mes=YYYY-MM` para consultar histórico de meses
anteriores (somente leitura — o valor_limite em vigor era o atual, pois não há versionamento
histórico do limite).

### Orçamento inativo

Quando `ativo = false`: não aparece no widget do painel, não gera alertas de notificação,
mas o registro é preservado para reativação posterior.

### Integração com notificações (tarefa 20)

Ao registrar ou editar um lançamento de despesa, o service de lançamentos verifica se existe
orçamento ativo para a categoria. Se o consumo do mês cruzar os limiares:
- 90% do limite → notificação `orcamento_critico` (uma vez por mês por orçamento)
- 100% do limite → notificação `orcamento_estourado` (uma vez por mês por orçamento)

Deduplicação: igual ao padrão da tarefa 20 (não repetir se já existe notificação do mesmo tipo
+ `dado_id` nas últimas 24h).

---

## Endpoints

### `GET /orcamentos`
- Autenticação: obrigatória
- Query params: `mes` (YYYY-MM, default mês atual), `incluir_inativos` (bool, default false)
- Response 200: lista de orçamentos com consumo calculado para o mês:
  ```
  {
    "id": UUID,
    "categoria": { "id": UUID, "nome": str, "icone_nome": str, "cor": str },
    "valor_limite": NUMERIC,
    "valor_gasto": NUMERIC,
    "percentual": NUMERIC,
    "saldo_disponivel": NUMERIC,   // valor_limite - valor_gasto (pode ser negativo)
    "status": "tranquilo" | "atencao" | "critico" | "estourado",
    "ativo": bool
  }
  ```

### `POST /orcamentos`
- Autenticação: obrigatória
- Body: `categoria_id`, `valor_limite`
- Validação: `valor_limite > 0`; `categoria_id` acessível ao usuário; sem orçamento já ativo
  para essa categoria (409 se duplicata)
- Response 201: orçamento criado

### `PUT /orcamentos/{id}`
- Autenticação: obrigatória — somente o dono
- Body: `valor_limite` (opt), `ativo` (opt)
- Response 200: orçamento atualizado

### `DELETE /orcamentos/{id}`
- Autenticação: obrigatória — somente o dono
- Exclusão física (sem soft-delete — orçamento não tem histórico próprio)
- Response 200

### `GET /orcamentos/resumo`
- Autenticação: obrigatória
- Query param: `mes` (YYYY-MM, default mês atual)
- Response 200: visão consolidada para o widget do painel:
  ```
  {
    "total_orcado": NUMERIC,     // soma de valor_limite dos ativos
    "total_gasto": NUMERIC,      // soma de valor_gasto de todos os orçamentos ativos
    "percentual_geral": NUMERIC,
    "em_atencao": int,           // count com status=atencao
    "em_critico": int,
    "estourados": int,
    "orcamentos": [...]          // array completo (igual GET /orcamentos)
  }
  ```

---

## Atualizar o painel (tarefa 09)

Adicionar ao response de `GET /painel`:

```json
"orcamento_mes": {
  "total_orcado": NUMERIC,
  "total_gasto": NUMERIC,
  "percentual_geral": NUMERIC,
  "em_atencao": int,
  "em_critico": int,
  "estourados": int
}
```

Widget "Orçamento" no painel: barra de progresso geral + contadores coloridos de alertas.
Clique → abre tela `/orcamento` ou `DrawerDetalheComponent` com os orçamentos do mês.

---

## Atualizar notificações (tarefa 20)

Adicionar dois novos tipos à tabela de tipos de notificação:

| `tipo` | Gatilho |
|---|---|
| `orcamento_critico` | Consumo atinge ≥ 90% do limite na criação/edição de lançamento |
| `orcamento_estourado` | Consumo ultrapassa 100% do limite na criação/edição de lançamento |

---

## Frontend

### Tela `/orcamento` (nova rota)

- Grade de cards, um por orçamento ativo
- Cada card:
  - Ícone + nome da categoria (com cor da categoria)
  - Barra de progresso com cor dinâmica conforme `status`
  - "R$ X gastos de R$ Y" + percentual
  - Saldo disponível (ou "R$ Z estourado" em vermelho se negativo)
  - Mês consultado (seletor de mês no topo da tela)
- Botão "+ Novo orçamento" → `ModalCriarOrcamentoComponent`
- Clicar em card → `DrawerDetalheComponent` com lançamentos daquela categoria no mês

### `ModalCriarOrcamentoComponent`

- Select de categoria (`CategoriaSelectorComponent` da tarefa 17) —
  filtra categorias que já têm orçamento ativo (não pode duplicar)
- Campo `valor_limite` (numérico, obrigatório) com ícone de calculadora
- Botões: Cancelar | Salvar
- Ao salvar: card aparece imediatamente na grade com consumo calculado

### Edição inline no card

- Clique no valor limite do card → input inline para editar `valor_limite`
- Confirmar com Enter ou clique fora → `PUT /orcamentos/{id}`
- Toggle ativo/inativo via switch no card

### Widget "Orçamento" no painel

- Barra de progresso geral (total_gasto / total_orcado)
- Linha de badges: "X atenção", "Y críticos", "Z estourados" (somente se > 0)
- Link "Ver orçamento completo" → `/orcamento`
- Clique no widget → abre tela `/orcamento`

### Indicador de orçamento nos modais de despesa (tarefa 07)

Ao selecionar uma categoria no modal de criação de despesa:
- Se existe orçamento ativo para aquela categoria: exibir abaixo do select
  "Orçamento: R$ X de R$ Y (Z%)" com cor conforme status atual
- Atualizado em tempo real ao digitar o valor da despesa (cálculo estimado local)

### `OrcamentosService` (Angular, singleton)

Métodos: `listar(mes)`, `resumo(mes)`, `criar(dados)`, `atualizar(id, dados)`, `excluir(id)`

---

## Verificação

```bash
# 1. Criar orçamento para alimentação
curl -s -X POST http://localhost:8000/orcamentos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"categoria_id":"<uuid-alimentacao>","valor_limite":"800.00"}' \
  | python3 -m json.tool
# esperado: 201; valor_gasto=0, percentual=0, status=tranquilo

# 2. Criar lançamentos na categoria
# criar despesa de 600 com categoria alimentação
# GET /orcamentos → valor_gasto=600, percentual=75, status=atencao

# 3. Criar despesa que estoura → notificação gerada
# criar despesa de 300 (total 900 de 800) → status=estourado
# GET /notificacoes → notificacao tipo=orcamento_estourado

# 4. Tentar criar segundo orçamento para mesma categoria → 409

# 5. Editar limite
curl -s -X PUT http://localhost:8000/orcamentos/$ID \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"valor_limite":"1000.00"}' | python3 -m json.tool
# esperado: 200; status volta a atencao (900 de 1000 = 90%)

# 6. Desativar orçamento
curl -s -X PUT http://localhost:8000/orcamentos/$ID \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ativo":false}' | python3 -m json.tool
# GET /orcamentos → não aparece (incluir_inativos=false padrão)

# 7. Painel inclui orcamento_mes
curl -s "http://localhost:8000/painel?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('orcamento_mes'))"

# 8. Histórico de mês anterior
curl -s "http://localhost:8000/orcamentos?mes=2026-10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: valor_gasto calculado com lançamentos de outubro
```

Frontend:
- Abrir `/orcamento` → grade de cards (vazia se sem orçamentos)
- Criar orçamento de Alimentação com limite R$ 800
- Criar despesa de Alimentação de R$ 600 → barra amarela (75%)
- Criar mais R$ 250 → barra vermelha + notificação no sino
- Painel → widget de orçamento com barra geral + badge "1 estourado"
- Abrir modal de nova despesa → selecionar Alimentação → indicador de orçamento aparece abaixo

---

## Fora do escopo

- Orçamento compartilhado com o parceiro (usar meta de limite_gasto da tarefa 14 para isso)
- Rollover de saldo não utilizado para o mês seguinte
- Orçamento por subcategoria
- Orçamento total mensal (sem categoria — apenas o consolidado já aparece no widget)
- Sugestão automática de limite baseada em histórico
- Orçamento de receita mínima esperada
