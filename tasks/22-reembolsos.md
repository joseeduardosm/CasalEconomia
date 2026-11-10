# Tarefa 22 — Reembolsos

## Contexto

Implementa o controle de lançamentos onde o usuário pagou algo por outra pessoa (que não é
necessariamente o parceiro cadastrado no casal) e espera ser reembolsado. Exemplos: pagar a
conta do restaurante por um amigo, adiantar o aluguel por um colega, comprar passagem e receber
metade de volta.

Diferença do compartilhamento (tarefas 07/08): o compartilhamento é entre usuários do sistema
com percentual; o reembolso é com qualquer pessoa (identificada por nome livre) e pode ser
parcial ao longo do tempo.

**Pré-requisito:** tarefas 01–21 concluídas.

---

## Novas colunas em `lancamentos`

| Campo | Tipo | Notas |
|---|---|---|
| `reembolsavel` | BOOLEAN | default `false`; apenas para `tipo = "despesa"` |
| `nome_devedor` | VARCHAR(120) | nome da pessoa que deve reembolsar |
| `valor_reembolsado` | NUMERIC(12,2) | default `0`; acumulado a cada entrada de reembolso |

### Status de reembolso (derivado, não persistido)

```
"pendente"           se reembolsavel=true e valor_reembolsado = 0
"parcialmente_pago"  se reembolsavel=true e 0 < valor_reembolsado < valor
"reembolsado"        se reembolsavel=true e valor_reembolsado >= valor
```

---

## Nova tabela

### `entradas_reembolso`

Registra cada entrada de reembolso recebida ao longo do tempo.

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `lancamento_id` | UUID FK → `lancamentos.id` CASCADE | sim | o lançamento de despesa reembolsável |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | quem registrou a entrada |
| `valor` | NUMERIC(12,2) | sim | valor recebido nesta entrada |
| `data` | DATE | sim | data do recebimento |
| `nota` | VARCHAR(200) | não | ex: "PIX recebido", "dinheiro" |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Regras de negócio

### Marcar lançamento como reembolsável

- Apenas `tipo = "despesa"` pode ser `reembolsavel = true`
- Ao ativar: `nome_devedor` torna-se obrigatório
- Lançamentos parcelados: `reembolsavel = true` se aplica à **série** inteira; cada parcela
  tem sua própria `valor_reembolsado` rastreada individualmente
- Reembolso não altera o valor do lançamento original; é um controle paralelo

### Registrar entrada de reembolso

- `valor` da entrada ≤ `lancamento.valor - valor_reembolsado` (não pode reembolsar além do total)
- Ao registrar: `lancamentos.valor_reembolsado += entrada.valor`
- Se `valor_reembolsado >= valor`: status passa para "reembolsado"

### Exclusão de entrada de reembolso

- Excluir entrada: `lancamentos.valor_reembolsado -= entrada.valor`
- Mínimo de `valor_reembolsado`: 0 (não pode ficar negativo)

### Visibilidade no painel e relatórios

- Widget "Reembolsos pendentes" no painel: soma dos `valor - valor_reembolsado` de todos os
  lançamentos `reembolsavel = true` com `status ≠ "reembolsado"`
- Relatório R1 (distribuição): lançamentos reembolsáveis entram normalmente no total de despesas;
  o "valor líquido" (descontando reembolsado) é exibido como informação secundária

---

## Endpoints

### `PATCH /lancamentos/{id}/reembolso`
- Autenticação: obrigatória — somente o dono do lançamento
- Body: `reembolsavel` (bool), `nome_devedor` (str)
- Response 200: lançamento atualizado com campos de reembolso

### `POST /lancamentos/{id}/reembolso/entradas`
- Autenticação: obrigatória — somente o dono
- Apenas para lançamentos `reembolsavel = true`
- Body: `valor`, `data`, `nota` (opt)
- Validação: `valor > 0` E `valor ≤ saldo_pendente`
- Response 201: entrada registrada + `valor_reembolsado` atualizado

### `DELETE /lancamentos/{id}/reembolso/entradas/{entrada_id}`
- Autenticação: obrigatória — somente o dono
- Response 200: entrada removida, `valor_reembolsado` recalculado

### `GET /lancamentos/reembolsos`
- Autenticação: obrigatória
- Query params: `status` (pendente/parcialmente_pago/reembolsado/todos — default: pendente+parcialmente_pago)
- Response 200: lista de lançamentos reembolsáveis com `status`, `valor_reembolsado`,
  `saldo_pendente`, `nome_devedor` e últimas 3 entradas

---

## Atualizar o painel (tarefa 09)

Adicionar ao response de `GET /painel`:

```
"reembolsos_pendentes": {
  "total": NUMERIC,     // soma de (valor - valor_reembolsado) dos pendentes
  "count": int          // número de lançamentos com reembolso em aberto
}
```

Widget compacto no painel: "R$ X a receber" com link → `/lancamentos/reembolsos`.

---

## Frontend

### Campos no modal de despesa (`ModalCriarDespesaComponent` — tarefa 07)

Adicionar seção colapsável "Este gasto será reembolsado?":
- Toggle "Marcar como reembolsável"
- Se ativado: campo `nome_devedor` (texto livre, obrigatório)
- Chip de status exibido na lista de lançamentos: `pendente` / `parcial` / `reembolsado`

### Tela `/lancamentos/reembolsos` (nova rota)

- Tabs: Pendentes / Parcialmente pagos / Todos
- `TabelaLancamentosComponent` com colunas: Descrição, Devedor, Data, Valor total,
  Reembolsado, Saldo pendente, Status
- Clicar em linha → detalhe do reembolso (`DetalheReembolsoComponent`)

### `DetalheReembolsoComponent` (drawer ou página)

- Dados do lançamento original
- Barra de progresso: valor_reembolsado / valor * 100%
- Lista de entradas com data, valor, nota
- Botão "+ Registrar recebimento"
- Botão "Excluir entrada" em cada item

### Widget "Reembolsos pendentes" no painel

- Card compacto com ícone `heroArrowUturnLeft` e valor total pendente
- Link → `/lancamentos/reembolsos`
- Clique abre `DrawerDetalheComponent` com lista dos pendentes

### `ReembolsosService` (Angular, singleton)

Métodos: `listar(filtros)`, `marcarReembolsavel(id, dados)`, `registrarEntrada(id, dados)`,
`excluirEntrada(lancamentoId, entradaId)`

---

## Verificação

```bash
# 1. Criar despesa e marcar como reembolsável
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"descricao":"Jantar","tipo":"despesa","valor":"200.00","data_lancamento":"2026-11-09","forma_pagamento":"cartao_credito","reembolsavel":true,"nome_devedor":"Carlos"}' \
  | python3 -m json.tool
# esperado: 201; reembolsavel=true, valor_reembolsado=0

# 2. Registrar entrada parcial de reembolso
curl -s -X POST http://localhost:8000/lancamentos/$ID/reembolso/entradas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"valor":"100.00","data":"2026-11-10","nota":"PIX"}' | python3 -m json.tool
# esperado: 201; valor_reembolsado=100; status="parcialmente_pago"

# 3. Registrar segunda entrada quitando o restante
# valor=100 → status="reembolsado"

# 4. Tentar registrar além do saldo → 422

# 5. Listar reembolsos pendentes
curl -s "http://localhost:8000/lancamentos/reembolsos?status=pendente" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 6. Painel inclui reembolsos_pendentes
curl -s "http://localhost:8000/painel?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('reembolsos_pendentes'))"
# esperado: { "total": 100.00, "count": 1 }
```

Frontend:
- Criar despesa marcada como reembolsável → aparece com chip "pendente" na lista
- Abrir detalhe → registrar recebimento parcial → chip muda para "parcial"
- Registrar valor restante → chip muda para "reembolsado" e some do widget do painel
- Widget do painel atualiza o valor pendente

---

## Fora do escopo

- Reembolso entre usuários do sistema (isso é o compartilhamento de lançamentos)
- Reembolso vinculado a lançamentos de receita
- Cobrança via PIX ou link de pagamento gerado pelo sistema
- Lembretes automáticos para o devedor
- Reembolso em moeda diferente do lançamento original
