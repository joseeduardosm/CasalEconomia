# Tarefa 14 — Metas Financeiras

## Contexto

Implementa a tela `/metas` com metas de economia e controle de gastos. Uma meta pode ser
individual (só o usuário acompanha) ou **compartilhada com o parceiro** (ambos contribuem e
acompanham o progresso juntos). O progresso é calculado a partir dos lançamentos reais —
sem campo de "valor poupado" manual.

**Pré-requisito:** tarefas 01–13 concluídas.

---

## Tipos de meta

| Tipo | Descrição |
|---|---|
| `economia` | Acumular um valor até uma data (ex: R$ 5.000 até dez/2027 para viagem) |
| `limite_gasto` | Não gastar mais que X em uma categoria por mês (ex: máx R$ 500 em restaurantes) |

---

## Novas tabelas

### `metas`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | dono da meta |
| `tipo` | VARCHAR(20) | sim | `economia` / `limite_gasto` |
| `nome` | VARCHAR(120) | sim | ex: "Viagem para Europa" |
| `valor_alvo` | NUMERIC(12,2) | sim | valor a acumular ou limite a não ultrapassar |
| `categoria` | VARCHAR(80) | não | categoria de lançamentos associada (para `limite_gasto`) |
| `data_inicio` | DATE | sim | início da vigência |
| `data_fim` | DATE | não | prazo final (nulo = sem prazo) |
| `compartilhada` | BOOLEAN | sim | default `false` |
| `arquivada_em` | TIMESTAMPTZ | não | soft-delete |
| `criado_em` | TIMESTAMPTZ | sim | |

### `contribuicoes_meta` (somente para `tipo = "economia"`)

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `meta_id` | UUID FK → `metas.id` CASCADE | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | quem contribuiu |
| `valor` | NUMERIC(12,2) | sim | valor da contribuição |
| `data` | DATE | sim | |
| `nota` | VARCHAR(200) | não | |
| `criado_em` | TIMESTAMPTZ | sim | |

**Por que `contribuicoes_meta` em vez de vincular a `lancamentos`?**
Metas de economia raramente mapeiam 1:1 para um lançamento específico — o usuário pode poupar
de forma difusa (receber salário e "guardar parte") ou de um investimento. Contribuições manuais
são mais práticas para o MVP.

---

## Regras de negócio

### Progresso de meta `economia`

```
valor_acumulado = SUM(contribuicoes_meta.valor WHERE meta_id=X)
percentual = valor_acumulado / valor_alvo * 100
dias_restantes = data_fim - hoje  (null se sem prazo)
ritmo_necessario = (valor_alvo - valor_acumulado) / meses_restantes  (se data_fim definida)
```

### Progresso de meta `limite_gasto`

```
valor_gasto_mes = SUM(lancamentos.valor WHERE tipo="despesa"
                      AND categoria=meta.categoria
                      AND data_lancamento ENTRE inicio_mes E fim_mes
                      AND usuario_id IN (meta.usuario_id + parceiro SE compartilhada))
percentual = valor_gasto_mes / valor_alvo * 100
status: "ok" se < 80%, "atencao" se 80–100%, "estourado" se > 100%
```

### Meta compartilhada
- `compartilhada = true` permite que o parceiro:
  - Visualize o progresso no próprio painel
  - Adicione contribuições (apenas em `economia`)
  - Veja lançamentos que impactam a meta (em `limite_gasto`)
- Apenas o dono (`usuario_id`) pode editar ou arquivar a meta
- A meta aparece na aba `/casal` (tarefa 13) como item de destaque

### Alerta de meta
- `limite_gasto` ≥ 80%: exibir badge amarelo na tela `/metas` e no widget de metas do painel
- `limite_gasto` > 100%: badge vermelho
- `economia` com `data_fim` próxima (≤ 30 dias) e progresso < 70%: badge laranja

---

## Endpoints

### `POST /metas`
- Autenticação: obrigatória
- Body: `nome`, `tipo`, `valor_alvo`, `categoria` (se limite_gasto), `data_inicio`, `data_fim`
  (opcional), `compartilhada` (bool)
- Response 201: meta criada

### `GET /metas`
- Autenticação: obrigatória
- Query param: `incluir_arquivadas` (bool, default false)
- Response 200: lista com progresso calculado para cada meta + `status` derivado

### `GET /metas/{id}`
- Autenticação: obrigatória
- Response 200: meta com progresso detalhado + contribuições (para `economia`) + histórico de
  gasto mensal nos últimos 6 meses (para `limite_gasto`)

### `PUT /metas/{id}`
- Autenticação: obrigatória — somente o dono pode editar
- Body: campos editáveis
- Response 200: meta atualizada

### `DELETE /metas/{id}`
- Autenticação: obrigatória — somente o dono
- Response 200: soft-delete via `arquivada_em`

### `POST /metas/{id}/contribuicoes`
- Autenticação: obrigatória — dono OU parceiro (se compartilhada)
- Apenas para `tipo = "economia"`
- Body: `valor`, `data`, `nota` (opcional)
- Response 201: contribuição registrada

### `DELETE /metas/{id}/contribuicoes/{contrib_id}`
- Autenticação: obrigatória — somente quem criou a contribuição
- Response 200: contribuição removida

---

## Atualizar o painel (tarefa 09)

Adicionar ao response de `GET /painel`:
```json
"metas_destaque": [
  {
    "id": UUID,
    "nome": str,
    "tipo": str,
    "percentual": NUMERIC,
    "status": "ok" | "atencao" | "estourado" | "em_andamento",
    "compartilhada": bool
  }
]
```
Máximo 3 metas: as com status mais crítico primeiro. Widget "Metas" no painel como nova linha
após os cards de resumo (ou integrado à segunda linha).

---

## Frontend

### Tela `/metas` (substituir placeholder)

- Lista de cards de metas
- Cada card: nome, tipo (chip), barra de progresso visual, valor acumulado / valor alvo,
  data prazo (se houver), status chip (ok/atenção/estourado), ícone de compartilhamento
- Filtro rápido: Todas / Economia / Limite de gasto / Compartilhadas
- Botão "+ Nova meta" → modal `ModalCriarMetaComponent`

### `ModalCriarMetaComponent`

- `nome` (texto, obrigatório)
- `tipo` (radio: "Meta de economia" / "Limite de gastos")
- `valor_alvo` (decimal; label dinâmico: "Valor a acumular" OU "Limite máximo")
- `categoria` (texto; visível apenas se `tipo = limite_gasto`)
- `data_inicio` (date, default hoje)
- `data_fim` (date, opcional)
- `compartilhada` (toggle; visível apenas se tem parceiro conectado)
- Botões: Cancelar | Salvar

### Tela detalhe `/metas/:id`

**Para `economia`:**
- Barra de progresso grande com % e "R$ X de R$ Y"
- Ritmo necessário: "Para atingir a meta, você precisa poupar R$ X/mês"
- Lista de contribuições com data, valor, nota e nome do contribuidor (se compartilhada)
- Botão "+ Registrar contribuição"
- Histórico em gráfico de barras mensais (contribuições por mês — Chart.js)

**Para `limite_gasto`:**
- Barra de progresso com cor dinâmica (verde → amarelo → vermelho)
- Gasto atual vs limite + percentual
- Lista dos últimos 10 lançamentos que impactaram a meta (da categoria configurada)
  usando `TabelaLancamentosComponent`
- Histórico: gráfico de barras com gasto vs limite nos últimos 6 meses

### Widget "Metas" no painel

- Exibe até 3 metas mais críticas com barra de progresso mini
- Link "Ver todas" → `/metas`

### `MetasService` (Angular, singleton)

Métodos: `listar(filtros)`, `criar(dados)`, `atualizar(id, dados)`, `arquivar(id)`,
`detalhe(id)`, `adicionarContribuicao(metaId, dados)`, `removerContribuicao(metaId, contribId)`

---

## Verificação

```bash
# 1. Criar meta de economia
curl -s -X POST http://localhost:8000/metas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"Viagem Europa","tipo":"economia","valor_alvo":"10000.00","data_fim":"2027-06-01","compartilhada":true}' \
  | python3 -m json.tool
# esperado: 201 com id, percentual=0

# 2. Registrar contribuição
curl -s -X POST http://localhost:8000/metas/$META_ID/contribuicoes \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"valor":"500.00","data":"2026-11-09"}' | python3 -m json.tool
# esperado: 201; GET /metas/:id mostra percentual=5

# 3. Criar meta de limite de gasto
curl -s -X POST http://localhost:8000/metas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"Restaurantes novembro","tipo":"limite_gasto","valor_alvo":"500.00","categoria":"Restaurante","data_inicio":"2026-11-01","data_fim":"2026-11-30"}' \
  | python3 -m json.tool

# 4. Criar despesa na categoria da meta → verificar impacto
# criar lancamento com categoria="Restaurante" valor=400
# GET /metas/:id → percentual=80, status="atencao"

# 5. Meta compartilhada visível para o parceiro
curl -s http://localhost:8000/metas -H "Authorization: Bearer $TOKEN_PARCEIRO" | python3 -m json.tool
# esperado: meta compartilhada aparece na lista do parceiro

# 6. Painel inclui metas em destaque
curl -s "http://localhost:8000/painel?mes=2026-11" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('metas_destaque'))"
# esperado: lista com até 3 metas

# 7. Contribuição do parceiro em meta compartilhada
curl -s -X POST http://localhost:8000/metas/$META_ID/contribuicoes \
  -H "Authorization: Bearer $TOKEN_PARCEIRO" -H "Content-Type: application/json" \
  -d '{"valor":"300.00","data":"2026-11-10"}' | python3 -m json.tool
# esperado: 201; GET /metas/:id mostra contribuição do parceiro

# 8. Parceiro tenta editar meta que não é dele → 403
```

Frontend:
- Abrir `/metas` → lista de cards com barras de progresso
- Criar meta de economia → progresso em 0%
- Registrar contribuição → barra avança
- Criar meta de limite de gasto com categoria → criar despesa nessa categoria → barra amarela
- Meta compartilhada aparece na lista do parceiro
- Painel → widget "Metas" exibe as mais críticas

---

## Fora do escopo

- Metas atreladas automaticamente a lançamentos (vínculo manual via contribuições)
- Notificação quando meta é atingida ou está em risco
- Metas de renda mínima mensal
- Sub-metas ou metas em cascata
- Integração com investimentos
- Sugestão automática de contribuição baseada em histórico
