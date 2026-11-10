# Tarefa 15 — Contas Bancárias

## Contexto

Implementa o módulo de contas bancárias (corrente, poupança, carteira, investimento). A tabela
`contas` é nova; o campo `conta_id` já existe em `lancamentos` desde as tarefas 07 e 08, mas
sem validação — esta tarefa o ativa.

O saldo de uma conta **não é persistido**: é sempre calculado como
`saldo_inicial + receitas liquidadas − despesas pagas` para aquela conta. Isso elimina a
inconsistência que o OpenMonetis tem quando o saldo persiste em paralelo com as transações.

**Pré-requisito:** tarefas 01–10 concluídas.

---

## Melhorias sobre o OpenMonetis

| # | Problema original | Decisão aqui |
|---|---|---|
| 1 | `balance` persistido em paralelo com transações | Saldo calculado em tempo real (sem coluna de saldo) |
| 2 | Ajuste manual de saldo é um tipo especial de lançamento | Sem tipo especial: se o saldo está errado, edita-se o lançamento |
| 3 | Sem extrato filtrado por conta | `GET /contas/{id}/extrato?mes=YYYY-MM` retorna só os lançamentos da conta |
| 4 | Sem distinção entre saldo disponível e saldo total | `saldo_disponivel` = somente lançamentos liquidados; `saldo_previsto` = todos (incluindo pendentes) |
| 5 | Delete físico apaga histórico de conta | `arquivado_em` timestamp — soft-delete; lançamentos vinculados permanecem |

---

## Tabela: `contas` (nova)

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `nome` | VARCHAR(80) | sim | ex: "Nubank Conta", "Carteira" |
| `tipo` | VARCHAR(20) | sim | `corrente/poupanca/investimento/carteira/outro` |
| `saldo_inicial` | NUMERIC(12,2) | sim | default 0; valor de abertura da conta no sistema |
| `cor` | VARCHAR(7) | sim | hex; default `"#3ba6f1"` |
| `icone_nome` | VARCHAR(40) | não | nome de ícone heroicons; default `"heroBuildingLibrary"` |
| `arquivado_em` | TIMESTAMPTZ | não | nulo = ativa; soft-delete |
| `criado_em` | TIMESTAMPTZ | sim | |

## `lancamentos` — ativar validação de `conta_id` (migration de constraint)

Adicionar constraint de FK verificada: se `conta_id` for informado, deve pertencer ao mesmo
`usuario_id` do lançamento. Implementado como verificação no service (não FK de banco, pois
a coluna já existe como nullable sem constraint).

---

## Regras de negócio

### Cálculo de saldo

```
saldo_disponivel =
  saldo_inicial
  + SUM(valor WHERE conta_id=X AND tipo="receita" AND liquidado=true)
  - SUM(valor WHERE conta_id=X AND tipo="despesa" AND liquidado=true)

saldo_previsto =
  saldo_inicial
  + SUM(valor WHERE conta_id=X AND tipo="receita")
  - SUM(valor WHERE conta_id=X AND tipo="despesa")
```

Lançamentos de cartão de crédito (`cartao_id IS NOT NULL`) **não entram** no saldo de conta —
o débito do cartão é o pagamento da fatura, registrado à parte.

### Validação de `conta_id` em lançamentos (ativar a partir desta tarefa)

Ao criar ou editar um lançamento com `conta_id`:
- 400 se `conta_id` não pertence ao `usuario_id` autenticado
- 400 se a conta está arquivada
- Aceitar `conta_id = null` (lançamento sem conta vinculada)

### Soft-delete

`DELETE /contas/{id}` preenche `arquivado_em`. Lançamentos vinculados permanecem intactos e
continuam associados à conta (histórico preservado). Conta arquivada não aceita novos
lançamentos (`conta_id` a ela → 400).

### Conta padrão

Sem conceito de "conta padrão" automática — o usuário escolhe explicitamente a cada lançamento.

---

## Endpoints

### `POST /contas`
- Autenticação: obrigatória
- Body: `nome`, `tipo`, `saldo_inicial` (string decimal, default `"0.00"`), `cor` (hex, opcional),
  `icone_nome` (opcional)
- Response 201: dados da conta criada

### `GET /contas`
- Autenticação: obrigatória
- Query param: `incluir_arquivadas` (bool, default false)
- Response 200: lista de contas com `saldo_disponivel` e `saldo_previsto` calculados

### `GET /contas/{id}`
- Autenticação: obrigatória
- Response 200: conta com saldos calculados
- Erros: 404, 403

### `PUT /contas/{id}`
- Autenticação: obrigatória
- Body: mesmos campos do POST
- Response 200: conta atualizada
- Erros: 404, 400 se arquivada

### `DELETE /contas/{id}`
- Autenticação: obrigatória
- Response 200: `{ "mensagem": "Conta arquivada." }`
- Comportamento: soft-delete via `arquivado_em`

### `GET /contas/{id}/extrato`
- Autenticação: obrigatória
- Query params: `mes` (YYYY-MM, obrigatório)
- Response 200:
  ```
  {
    "conta": { id, nome, tipo, cor },
    "saldo_anterior": NUMERIC,       // saldo_disponivel até o mês anterior
    "entradas": NUMERIC,             // receitas liquidadas no mês
    "saidas": NUMERIC,               // despesas pagas no mês
    "saldo_final": NUMERIC,          // saldo_disponivel até o fim do mês
    "lancamentos": [...]             // todos os lançamentos do mês para esta conta
  }
  ```

---

## Atualizar o sincronizador (tarefa 05)

Nenhuma mudança no sincronizador. A validação de `conta_id` é feita no service de lançamentos
ao criar/editar.

---

## Atualizar o painel (tarefa 09)

Adicionar ao response de `GET /painel`:
```json
"contas": [
  {
    "id": UUID,
    "nome": str,
    "tipo": str,
    "cor": str,
    "saldo_disponivel": NUMERIC,
    "saldo_previsto": NUMERIC
  }
]
```
Apenas contas ativas (`arquivado_em IS NULL`). Lista ordenada por `criado_em ASC`.

O `PainelComponent` ganha um widget "Minhas contas" (ver Frontend).

---

## Frontend

### Tela `/contas` (substituir placeholder da tarefa 03)

- Grid de cards, um por conta
- Cada card: faixa colorida no topo com `cor` da conta, ícone + nome, tipo (chip), saldo
  disponível em destaque, saldo previsto em cinza abaixo
- Botão global "+ Nova conta"
- Botão por card: "Ver extrato" → `/contas/:id/extrato` e "Editar"
- Tipos → rótulos PT-BR: `corrente` = "Conta Corrente", `poupanca` = "Poupança",
  `investimento` = "Investimento", `carteira` = "Carteira", `outro` = "Outro"

### Modal `ModalCriarContaComponent`

- `nome` (texto, obrigatório)
- `tipo` (select: Conta Corrente, Poupança, Investimento, Carteira, Outro)
- `saldo_inicial` (decimal, default 0; label: "Saldo inicial ao entrar no app")
- `cor` (color picker simples — 8 opções predefinidas em chips clicáveis)
- `icone_nome` (select com 6 opções de ícones heroicons para conta)
- Botões: Cancelar | Salvar

### Tela `/contas/:id/extrato`

- Cabeçalho: nome da conta + cor + saldo disponível
- Seletor de mês (mesmo padrão do `BarraTopoComponent`)
- Resumo: "Entradas R$ X · Saídas R$ Y · Saldo final R$ Z"
- Lista de lançamentos do mês: descrição, data, valor (+ verde / − vermelho), status (liquidado/pendente)
- Botão "← Voltar para contas"

### Widget "Minhas contas" no `/painel`

- Adicionado ao layout do painel após a Row 1 (resumo do mês) ou integrado na Row 2
- Lista horizontal de cards compactos (scroll horizontal no mobile)
- Cada card: cor, nome, saldo disponível
- Link "Ver todas" → `/contas`
- Se sem contas: "Nenhuma conta cadastrada. [+ Adicionar conta]"

### `ContaService` (Angular, singleton)
Métodos: `listar(incluirArquivadas?)`, `criar(dados)`, `atualizar(id, dados)`, `arquivar(id)`,
`detalhe(id)`, `extrato(id, mes)`

---

## Verificação

```bash
# 1. Tabela criada
psql -U postgres casaleconomia_dev -c "\dt contas"
# esperado: tabela contas

# 2. Criar conta corrente
curl -s -X POST http://localhost:8000/contas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"Nubank","tipo":"corrente","saldo_inicial":"1500.00","cor":"#8a05be"}' \
  | python3 -m json.tool
# esperado: 201 com id; saldo_disponivel=1500.00, saldo_previsto=1500.00

CONTA_ID=<id-retornado>

# 3. Criar lançamento vinculado à conta (receita)
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"descricao\":\"Salário\",\"valor\":\"3000.00\",\"data_lancamento\":\"2026-11-05\",\"tipo\":\"receita\",\"forma_pagamento\":\"transferencia\",\"conta_id\":\"$CONTA_ID\",\"liquidado\":true}" \
  | python3 -m json.tool
# esperado: 201

# 4. Verificar saldo atualizado
curl -s http://localhost:8000/contas/$CONTA_ID -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: saldo_disponivel=4500.00 (1500 inicial + 3000 receita)

# 5. Lançamento com conta de outro usuário → 400
# esperado: 400

# 6. Lançamento com conta arquivada → 400
curl -s -X DELETE http://localhost:8000/contas/$CONTA_ID -H "Authorization: Bearer $TOKEN"
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"descricao\":\"Teste\",\"valor\":\"50.00\",\"data_lancamento\":\"2026-11-09\",\"tipo\":\"despesa\",\"conta_id\":\"$CONTA_ID\"}" \
  | python3 -m json.tool
# esperado: 400

# 7. Extrato
curl -s "http://localhost:8000/contas/$CONTA_ID/extrato?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: entradas=3000.00, saidas=0, saldo_final=4500.00, lancamentos com 1 item

# 8. Painel inclui contas
curl -s "http://localhost:8000/painel?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('contas'))"
# esperado: lista com a conta criada e seus saldos
```

Frontend:
- Abrir `/contas` → grid com a conta criada
- Criar nova conta → aparece no grid com saldo inicial correto
- Criar lançamento de despesa com `conta_id` → saldo diminui ao recarregar
- Extrato do mês → lista os lançamentos com saldo inicial, entradas, saídas e saldo final
- Painel → widget "Minhas contas" exibe as contas com saldos

---

## Fora do escopo

- Conciliação bancária (importação de OFX/CSV)
- Transferência entre contas (tarefa futura)
- Contas compartilhadas do casal (cada usuário tem suas próprias)
- Metas de saldo por conta
- Integração com open banking
- Histórico de edições de saldo inicial
