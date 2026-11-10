# Tarefa 13 — Visão Compartilhada do Casal

## Contexto

Implementa a tela `/casal` com a visão financeira consolidada do casal: lançamentos de ambos,
gráfico de evolução mensal, linha do tempo e o módulo de **fechamento** — o mecanismo que calcula
quem deve quanto a quem ao final de um período, considerando todos os lançamentos compartilhados
e as porcentagens negociadas.

O "fechamento" resolve o problema central do casal: X pagou coisas que Y deveria ter pago parte,
e Y pagou coisas que X deveria ter pago parte. O sistema calcula o saldo líquido e diz exatamente
qual transferência quita tudo.

**Pré-requisito:** tarefas 01–12 concluídas. Requer que pelo menos um usuário tenha parceiro
conectado (`conexoes_casal`).

---

## Conceito de Fechamento

### O problema
- X criou despesa de R$ 300 (supermercado) com 50% compartilhado → Y deve R$ 150 a X
- Y criou despesa de R$ 200 (conta de luz) com 50% compartilhado → X deve R$ 100 a Y
- Sem fechamento: dois débitos separados
- Com fechamento: Y deve R$ 50 a X (saldo líquido: 150 − 100)

### Regra de cálculo
```
Para cada lançamento compartilhado aceito no período:
  - Dono do lançamento: "credor" pelo valor_compartilhado
  - Parceiro que aceitou: "devedor" pelo valor_compartilhado

Saldo de X em relação a Y =
  SUM(valor_compartilhado WHERE dono=X AND parceiro_aceitou=Y)
  - SUM(valor_compartilhado WHERE dono=Y AND parceiro_aceitou=X)

Se saldo > 0: Y deve pagar X esse valor
Se saldo < 0: X deve pagar Y o valor absoluto
Se saldo = 0: quites
```

### Escopo do fechamento
- Período: mês ou intervalo personalizado
- Apenas lançamentos com `lancamentos_parceiro.status = "aceito"` entram no cálculo
- Lançamentos ignorados ou pendentes **não entram**

### Registrar o fechamento
Ao efetuar o pagamento do saldo, criar um lançamento de tipo `transferencia` (tarefa futura)
**OU** simplesmente marcar o fechamento como "quitado" com data, sem criar lançamento.
Nesta tarefa: registrar como "quitado" com data e valor — sem lançamento de transferência.

---

## Novas tabelas

### `fechamentos`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id_1` | UUID FK → `users.id` CASCADE | sim | um dos dois usuários do casal |
| `usuario_id_2` | UUID FK → `users.id` CASCADE | sim | o outro |
| `mes_inicio` | VARCHAR(7) | sim | `"2026-11"` |
| `mes_fim` | VARCHAR(7) | sim | `"2026-11"` (pode ser mesmo mês) |
| `valor_saldo` | NUMERIC(12,2) | sim | positivo = `usuario_id_1` recebe de `usuario_id_2`; negativo = inverso |
| `quitado_em` | TIMESTAMPTZ | não | preenchido ao marcar como quitado |
| `quitado_por` | UUID FK → `users.id` | não | quem marcou como quitado |
| `criado_em` | TIMESTAMPTZ | sim | |
| `criado_por` | UUID FK → `users.id` | sim | quem gerou o fechamento |

---

## Endpoints

### `GET /casal/lancamentos`
- Autenticação: obrigatória
- Query params: `mes` (YYYY-MM), `tipo` (receita/despesa/todos)
- Response 200: lançamentos do usuário autenticado **e** do parceiro para o mês, cada um
  com `dono: "eu" | "parceiro"` e `nome_dono: str`
- Apenas usuários com parceiro conectado podem acessar (403 se sem parceiro)

### `GET /casal/evolucao`
- Autenticação: obrigatória
- Query params: `meses` (3/6/12, default 6)
- Response 200: por mês:
  ```
  {
    "mes": "2026-11",
    "meu_total_despesas": NUMERIC,
    "meu_total_receitas": NUMERIC,
    "parceiro_total_despesas": NUMERIC,
    "parceiro_total_receitas": NUMERIC,
    "total_compartilhado": NUMERIC   // soma dos valor_compartilhado aceitos
  }
  ```

### `GET /casal/fechamento/preview`
- Autenticação: obrigatória
- Query params: `mes_inicio` (YYYY-MM), `mes_fim` (YYYY-MM)
- Response 200:
  ```
  {
    "quem_deve": "eu" | "parceiro" | "quites",
    "valor": NUMERIC,
    "nome_devedor": str,
    "nome_credor": str,
    "detalhes": [
      {
        "descricao": str,
        "data": DATE,
        "valor_total": NUMERIC,
        "valor_compartilhado": NUMERIC,
        "pago_por": str,
        "devo_a": str
      }
    ]
  }
  ```

### `POST /casal/fechamento`
- Autenticação: obrigatória
- Body: `mes_inicio`, `mes_fim`
- Response 201: fechamento criado com `valor_saldo`

### `POST /casal/fechamento/{id}/quitar`
- Autenticação: obrigatória
- Response 200: fechamento marcado como quitado

### `GET /casal/fechamentos`
- Autenticação: obrigatória
- Response 200: histórico de fechamentos do casal (recentes primeiro)

---

## Frontend

### Tela `/casal` (substituir placeholder)

Abas: **Lançamentos · Evolução · Fechamento**

---

#### Aba "Lançamentos"

- Seletor de mês (do `BarraTopoComponent`)
- `TabelaLancamentosComponent` com lançamentos de ambos
- Coluna extra "Quem lançou" com nome/avatar do dono
- Filtro rápido: Todos / Meus / Do parceiro / Compartilhados
- Totais separados por pessoa no rodapé

---

#### Aba "Evolução"

- Seletor: últimos 3 / 6 / 12 meses
- **Gráfico de barras agrupadas** (Chart.js): por mês, duas barras (Eu / Parceiro) para despesas
  — cor azul para o usuário, cor rosa/laranja para o parceiro
- Abaixo do gráfico: linha do tempo mensal com os eventos mais relevantes de cada mês:
  - Mês com maior gasto do usuário
  - Mês com maior receita
  - Meses com fechamento quitado (marcador verde)
- Tabela de comparativo mês a mês:
  colunas ordenáveis (Mês, Minhas despesas, Despesas do parceiro, Total compartilhado)

---

#### Aba "Fechamento"

**Painel de preview (topo):**
- Seletores `mes_inicio` e `mes_fim`
- Botão "Calcular" → `GET /casal/fechamento/preview`
- Resultado: card destacado mostrando "João deve R$ 50,00 para Maria" OU "Vocês estão quites"
- Botão "Registrar fechamento" → `POST /casal/fechamento` → confirmar
- Botão "Marcar como quitado" → `POST /casal/fechamento/{id}/quitar` (após registrar)

**Detalhe do cálculo:**
- Tabela com cada lançamento compartilhado que entrou no cálculo:
  Descrição, Data, Valor total, Valor compartilhado, Pago por, Deve a
- Totais por pessoa na última linha

**Histórico de fechamentos:**
- Lista de fechamentos anteriores: período, valor, quem devia a quem, status (pendente/quitado),
  data de quitação

---

## Verificação

```bash
# 1. Lançamentos do casal (mês atual)
curl -s "http://localhost:8000/casal/lancamentos?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lançamentos de ambos com campo dono="eu"/"parceiro"

# 2. Evolução dos últimos 6 meses
curl -s "http://localhost:8000/casal/evolucao?meses=6" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: array de 6 meses com totais de cada um

# 3. Preview do fechamento
curl -s "http://localhost:8000/casal/fechamento/preview?mes_inicio=2026-11&mes_fim=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: quem_deve, valor, detalhes com lançamentos compartilhados aceitos

# 4. Registrar fechamento
curl -s -X POST http://localhost:8000/casal/fechamento \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"mes_inicio":"2026-11","mes_fim":"2026-11"}' | python3 -m json.tool
# esperado: 201 com id e valor_saldo

# 5. Quitar
curl -s -X POST http://localhost:8000/casal/fechamento/$ID/quitar \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: quitado_em preenchido

# 6. Usuário sem parceiro → 403
# esperado: 403 "Você não tem um parceiro conectado"
```

Frontend:
- Aba "Lançamentos" → ver lançamentos de ambos lado a lado
- Aba "Evolução" → gráfico com barras agrupadas; linha do tempo abaixo
- Aba "Fechamento" → calcular → ver resultado; registrar → aparece no histórico
- Quitar → histórico atualiza com data de quitação

---

## Fora do escopo

- Desconectar o casal
- Fechamentos parciais (selecionar quais lançamentos entram)
- Integração automática com transferência bancária
- Notificação ao parceiro quando fechamento é registrado
- Múltiplos casais / grupos
