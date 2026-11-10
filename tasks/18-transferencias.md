# Tarefa 18 — Transferências entre Contas

## Contexto

Implementa a movimentação de dinheiro entre duas contas bancárias do próprio usuário.
Exemplo: mover R$ 500 da conta corrente para a poupança, ou da poupança para a conta de
investimentos.

Uma transferência não é receita nem despesa — é um deslocamento de saldo. No entanto, é
representada como **dois lançamentos espelhados** (um débito na conta de origem e um crédito
na conta de destino) para manter o registro contábil rastreável e permitir que o extrato de
cada conta mostre a movimentação.

**Pré-requisito:** tarefas 01–17 concluídas. Requer tarefas 15 (contas) e 08 (lancamentos).

---

## Conceito contábil

### Dois lançamentos, um grupo

```
Transferência de R$ 500 — Corrente → Poupança

  lancamentos:
    id=A: tipo=despesa, valor=500, conta_id=corrente, transferencia_id=T1, par_id=B
    id=B: tipo=receita, valor=500, conta_id=poupanca,  transferencia_id=T1, par_id=A
```

- `transferencia_id` vincula os dois lançamentos ao mesmo evento de transferência
- `par_id` referência cruzada: cada lançamento aponta para o seu espelho
- Excluir qualquer um dos dois invalida a transferência (exclui ambos em cascata)
- Editar valor/data: sempre via endpoint da transferência — nunca editar apenas um lado

### Impacto no saldo de conta

- Conta de origem: `saldo_disponivel` reduz pelo valor
- Conta de destino: `saldo_disponivel` aumenta pelo valor
- Ambos os lançamentos criados com `liquidado = true` (transferências são imediatas)

---

## Novas colunas em `lancamentos`

| Campo | Tipo | Notas |
|---|---|---|
| `transferencia_id` | UUID FK → `transferencias.id` | nulo para lançamentos avulsos |
| `par_id` | UUID FK → `lancamentos.id` | id do lançamento espelho |

## Nova tabela

### `transferencias`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | dono |
| `conta_origem_id` | UUID FK → `contas.id` | sim | conta de débito |
| `conta_destino_id` | UUID FK → `contas.id` | sim | conta de crédito; ≠ conta_origem_id |
| `valor` | NUMERIC(12,2) | sim | valor movimentado |
| `data_transferencia` | DATE | sim | data do evento |
| `nota` | VARCHAR(500) | não | |
| `lancamento_origem_id` | UUID FK → `lancamentos.id` | sim | o lançamento de débito |
| `lancamento_destino_id` | UUID FK → `lancamentos.id` | sim | o lançamento de crédito |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Regras de negócio

### Validações na criação

- `conta_origem_id ≠ conta_destino_id` — transferência para a mesma conta: 400
- Ambas as contas devem pertencer ao `usuario_id` autenticado — 400 se não forem dele
- Nenhuma das contas pode estar arquivada — 400
- `valor > 0` — 400 se zero ou negativo

### Criação atômica

A criação de uma transferência é uma operação atômica em banco:
1. Criar registro em `transferencias`
2. Criar `lancamento` de despesa na conta de origem
3. Criar `lancamento` de receita na conta de destino
4. Preencher `lancamento_origem_id`, `lancamento_destino_id` em `transferencias`
5. Preencher `transferencia_id` e `par_id` nos dois lançamentos

Falha em qualquer passo: rollback completo.

### Edição

- Apenas `nota` e `data_transferencia` podem ser editados via `PUT /transferencias/{id}`
- Para mudar `valor` ou `contas`: deve-se excluir e recriar a transferência
- Valor e contas não são editáveis para evitar inconsistências contábeis

### Exclusão

- `DELETE /transferencias/{id}`: exclui os dois lançamentos espelho + o registro de transferência
- Se algum dos lançamentos espelho foi deletado avulsamente (cenário inválido): exclusão da
  transferência remove o restante e o registro em `transferencias`

### Relatórios e saldo

- Lançamentos de transferência **não entram** em relatórios de distribuição (R1) nem totais de
  receita/despesa do painel — seriam contabilizados duas vezes
- O extrato de conta (tarefa 15) **inclui** transferências com rótulo "Transferência de/para [nome conta]"
- O filtro padrão de `/lancamentos` **exclui** lançamentos com `transferencia_id` preenchido;
  filtro opcional `incluir_transferencias=true` para mostrá-los

---

## Endpoints

### `POST /transferencias`
- Autenticação: obrigatória
- Body: `conta_origem_id`, `conta_destino_id`, `valor`, `data_transferencia`, `nota` (opt)
- Response 201: transferência criada com IDs dos dois lançamentos gerados

### `GET /transferencias`
- Autenticação: obrigatória
- Query params: `mes` (YYYY-MM), `conta_id` (filtrar por conta específica)
- Response 200: lista de transferências com `nome_conta_origem`, `nome_conta_destino`

### `GET /transferencias/{id}`
- Autenticação: obrigatória
- Response 200: detalhe com os dois lançamentos vinculados

### `PUT /transferencias/{id}`
- Autenticação: obrigatória — somente o dono
- Body: `nota`, `data_transferencia`
- Response 200: transferência atualizada

### `DELETE /transferencias/{id}`
- Autenticação: obrigatória — somente o dono
- Response 200: transferência e lançamentos espelho excluídos

---

## Integração com fechamento do casal (tarefa 13)

A tarefa 13 sugere que o pagamento de um fechamento poderia gerar um lançamento de transferência.
Com esta tarefa implementada:
- O botão "Marcar como quitado" em `POST /casal/fechamento/{id}/quitar` recebe um parâmetro
  opcional `conta_id` — se fornecido, cria automaticamente uma transferência (ou lançamento de
  despesa/receita avulso) representando o pagamento do saldo do fechamento.

---

## Frontend

### Entrada no modal de lançamentos (tarefas 07/08)

Adicionar terceiro tipo no FAB ou no modal: "Transferência"

### `ModalTransferenciaComponent`

- Seletor `conta_origem_id` (dropdown de contas do usuário, excluindo arquivadas)
- Seletor `conta_destino_id` (idem; opções filtradas para excluir a conta de origem selecionada)
- Campo `valor` com ícone de calculadora (igual tarefas 07/08)
- Campo `data_transferencia` (date, default hoje)
- Campo `nota` (textarea, opcional)
- Botões: Cancelar | Confirmar transferência
- Após confirmar: exibir confirmação "R$ X transferido de [Origem] para [Destino]"

### Tela `/lancamentos`

- Filtro existente "Todos / Despesas / Receitas" ganha nova aba "Transferências"
- Na aba "Transferências": `TabelaLancamentosComponent` com colunas
  Descrição (ex: "→ Poupança"), Data, Valor, Conta Origem, Conta Destino
- Por padrão, transferências não aparecem nas abas Despesas nem Receitas

### Extrato de conta `/contas/:id/extrato` (tarefa 15)

- Lançamentos de transferência aparecem com ícone `heroArrowsRightLeft` e rótulo
  "Transferência recebida de [Conta]" ou "Transferência para [Conta]"
- Cor neutra (cinza) em vez de vermelho/verde para distinguir de receitas/despesas reais

### Painel — contas

- Widget de contas no painel (tarefa 15) não muda: `saldo_disponivel` já inclui transferências
  no cálculo (são lançamentos com `liquidado=true`)

### `TransferenciasService` (Angular, singleton)

Métodos: `listar(filtros)`, `criar(dados)`, `atualizar(id, dados)`, `excluir(id)`, `detalhe(id)`

---

## Verificação

```bash
# 1. Criar transferência
curl -s -X POST http://localhost:8000/transferencias \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"conta_origem_id":"<uuid-corrente>","conta_destino_id":"<uuid-poupanca>","valor":"500.00","data_transferencia":"2026-11-09"}' \
  | python3 -m json.tool
# esperado: 201 com lancamento_origem_id e lancamento_destino_id

# 2. Verificar saldo das contas
curl -s http://localhost:8000/contas -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: corrente com saldo -500, poupança com saldo +500

# 3. Extrato da conta de origem inclui a transferência
curl -s "http://localhost:8000/contas/<corrente>/extrato?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: item com descricao="Transferência para Poupança"

# 4. Excluir transferência → ambos os lançamentos removidos, saldos voltam ao normal

# 5. Tentar transferir para mesma conta → 400
# 6. Tentar usar conta de outro usuário → 400 (ownership check)
# 7. Painel com relatório R1 → transferências não aparecem no total de despesas
```

Frontend:
- FAB ou modal com opção "Transferência"
- Preencher R$ 500 de Corrente para Poupança → confirmar
- Extrato da corrente mostra saída; extrato da poupança mostra entrada
- Aba "Transferências" em `/lancamentos` lista o evento
- Painel: saldos das contas atualizados corretamente

---

## Fora do escopo

- Transferências agendadas para data futura
- Transferências entre usuários do casal (isso é o fechamento — tarefa 13)
- Conversão de moeda
- Transferências recorrentes (combinação com tarefa 16 — futura)
- TED/DOC/PIX com comprovante anexado (tarefa 23 cobre anexos)
