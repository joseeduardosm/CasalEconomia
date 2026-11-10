# Tarefa 06 — Cartões de Crédito

## Contexto

Implementa o módulo de cartões de crédito com gestão de faturas mensais. O usuário cadastra seus
cartões informando nome, bandeira, limite, dia de fechamento e dia de vencimento. O sistema gera
automaticamente as faturas dos próximos 3 meses ao criar ou editar um cartão. Lançamentos podem
ser vinculados a um cartão e o sistema determina automaticamente em qual fatura a despesa cai.

Baseado no fluxo de cartões do OpenMonetis (`cards.ts`, `invoices.ts`), com cinco melhorias
estruturais descritas abaixo.

**Pré-requisito:** tarefas 01 a 05 concluídas.

---

## Melhorias sobre o OpenMonetis

| # | Problema original | Decisão aqui |
|---|---|---|
| 1 | Fatura só persiste ao pagar | `faturas` sempre criada (mês atual + 3 futuros ao criar/editar cartão) |
| 2 | "Parcialmente pago" é implícito | Status `"parcialmente_paga"` explícito na tabela |
| 3 | `closingDate` pode cair em fim de semana | Campo `fechar_em_dia_util` — avança fechamento para segunda, igual ao vencimento |
| 4 | Delete físico apaga histórico | `arquivado_em` timestamp — soft-delete com dados preservados |
| 5 | Histórico de fatura pobre | Histórico inclui `status`, `valor_pago`, `data_vencimento` além de período e valor |

---

## Tabelas a criar

### `cartoes`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `nome` | VARCHAR(120) | sim | |
| `bandeira` | VARCHAR(20) | sim | `visa/mastercard/elo/amex/hipercard/outro` |
| `limite` | NUMERIC(12,2) | sim | positivo |
| `dia_fechamento` | INTEGER | sim | entre 1 e 28 |
| `dia_vencimento` | INTEGER | sim | entre 1 e 28 |
| `fechar_em_dia_util` | BOOLEAN | sim | default `false` |
| `cor` | VARCHAR(7) | sim | hex, ex: `"#3ba6f1"`, default `"#3ba6f1"` |
| `anotacao` | VARCHAR(1000) | não | |
| `arquivado_em` | TIMESTAMPTZ | não | nulo = ativo; preenchido ao arquivar |
| `criado_em` | TIMESTAMPTZ | sim | |

### `faturas`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `cartao_id` | UUID FK → `cartoes.id` CASCADE | sim | índice |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | redundante, mas evita JOIN em queries diretas |
| `periodo` | VARCHAR(7) | sim | `"2026-11"` — único por `(cartao_id, periodo)` |
| `data_fechamento` | DATE | sim | calculada pelo service |
| `data_vencimento` | DATE | sim | calculada pelo service |
| `valor_pago` | NUMERIC(12,2) | sim | default 0 |
| `status` | VARCHAR(20) | sim | default `"aberta"` |
| `criado_em` | TIMESTAMPTZ | sim | |

### `lancamentos` — adicionar 2 colunas (migration separada)

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `cartao_id` | UUID FK → `cartoes.id` SET NULL | não | preenchido quando o lançamento é uma compra no cartão |
| `periodo_fatura` | VARCHAR(7) | não | ex: `"2026-11"` — calculado ao criar |

---

## Regras de negócio

### Cálculo de datas

**Vencimento:** no `dia_vencimento` do mês. Se cair em sábado ou domingo, avança para segunda-feira.
Usar `calendar.monthrange` para garantir que o dia existe no mês (máx. 28 é suficiente).

**Fechamento:** no `dia_fechamento` do mês **anterior** ao vencimento. Se `dia_fechamento >= dia_vencimento`, recua mais um mês. Se `fechar_em_dia_util=true`, aplica a mesma regra de avanço para segunda.

### Qual fatura recebe um lançamento

Ao criar lançamento com `cartao_id`:
1. Busca a fatura do período atual para o cartão
2. Se `data_lancamento > data_fechamento` da fatura atual → `periodo_fatura` = mês seguinte
3. Caso contrário → `periodo_fatura` = mês atual

### Geração automática de faturas (`_garantir_faturas`)

Chamada em: criação de cartão, edição de cartão, e pelo sincronizador a cada execução.
Cria faturas para: mês atual + 3 meses futuros. Idempotente — `get_or_create` por `(cartao_id, periodo)`.

### Status da fatura

Calculado no service a cada leitura e persistido:

```
valor_total = SUM(lancamentos.valor WHERE cartao_id=X AND periodo_fatura=Y)

se valor_pago >= valor_total AND valor_total > 0  → "paga"
se valor_pago > 0                                 → "parcialmente_paga"
se hoje > data_vencimento                         → "vencida"
se hoje > data_fechamento                         → "fechada"
senão                                             → "aberta"
```

### Soft-delete

`DELETE /cartoes/{id}` preenche `arquivado_em`. Listagem padrão exclui arquivados.
Cartão arquivado não pode ser editado.

### Pagamento

MVP: acumula `valor_pago`. Rejeita pagamento superior ao valor restante. Sem integração com conta bancária nesta tarefa.

---

## Endpoints

### `POST /cartoes`
- Autenticação: obrigatória
- Body: `nome`, `bandeira`, `limite` (string decimal), `dia_fechamento`, `dia_vencimento`, `fechar_em_dia_util` (bool, opcional), `cor` (hex, opcional), `anotacao` (opcional)
- Response 201: dados do cartão criado
- Comportamento: cria cartão + chama `_garantir_faturas`

### `GET /cartoes`
- Autenticação: obrigatória
- Query param: `incluir_arquivados` (bool, default false)
- Response 200: lista de cartões com `fatura_atual` e `limite_disponivel` embutidos
- `fatura_atual`: `{ fatura_id, periodo, data_vencimento, valor_total, valor_pago, status }`
- `limite_disponivel`: `limite - gasto_mes_atual`

### `PUT /cartoes/{id}`
- Autenticação: obrigatória
- Body: mesmos campos do POST
- Response 200: dados atualizados
- Erros: 404, 400 se arquivado
- Comportamento: atualiza + chama `_garantir_faturas` com novas configurações

### `DELETE /cartoes/{id}`
- Autenticação: obrigatória
- Response 200: mensagem de confirmação
- Comportamento: soft-delete via `arquivado_em`

### `GET /faturas/{id}`
- Autenticação: obrigatória
- Response 200: fatura com `valor_total` (calculado), `valor_restante`, `status` e lista de `lancamentos` do período
- Recalcula e persiste o `status` a cada leitura

### `POST /faturas/{id}/pagar`
- Autenticação: obrigatória
- Body: `valor` (string decimal)
- Response 200: `{ mensagem, valor_pago, valor_restante, status }`
- Erros: 400 se fatura já paga, 400 se valor > restante

### `GET /faturas/cartao/{cartao_id}/historico`
- Autenticação: obrigatória
- Response 200: lista com `{ fatura_id, periodo, data_vencimento, valor_total, valor_pago, status }` para todas as faturas do cartão, do mais recente ao mais antigo

---

## Atualizar o sincronizador (tarefa 05)

A função `executar_sincronizacao` deve também chamar `_garantir_faturas` para cada cartão ativo
de usuários com parceiro conectado. Isso garante que novos meses sempre terão fatura criada.

---

## Frontend

### Tela `/cartoes` (listagem)
- Grid de cards visuais, um por cartão
- Cada card mostra: faixa colorida no topo com a cor do cartão, nome, bandeira (chip), limite disponível (destaque), gasto do mês, status da fatura atual (chip colorido por status), data de vencimento
- Botões por card: "Ver fatura" (vai para `/cartoes/:id/fatura?fatura_id=X`) e "Editar"
- Botão global "+ Novo cartão" no topo
- Status → cores: aberta=azul, fechada=cinza, parcialmente_paga=amarelo, paga=verde, vencida=vermelho

### Tela `/cartoes/:id/fatura`
- Exibe fatura identificada pelo query param `fatura_id`
- Resumo: valor total, valor pago, valor restante (destaque), status, data de vencimento
- Formulário de pagamento: campo de valor + botão "Pagar" (oculto quando status="paga")
- Lista de lançamentos do período: descrição, data, valor
- Botão "← Voltar para cartões"

### `CartaoService` (Angular, singleton)
- Métodos: `listar()`, `criar(dados)`, `atualizar(id, dados)`, `arquivar(id)`, `detalheFatura(faturaId)`, `pagarFatura(faturaId, valor)`, `historico(cartaoId)`

---

## Verificação

```bash
# 1. Tabelas
psql -U postgres casaleconomia_dev -c "\dt"
# esperado: cartoes, faturas; \d lancamentos mostra cartao_id e periodo_fatura

# 2. Criar cartão
curl -s -X POST http://localhost:8000/cartoes \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"Nubank","bandeira":"mastercard","limite":"5000.00","dia_vencimento":10,"dia_fechamento":3,"cor":"#8a05be"}' \
  | python3 -m json.tool
# esperado: 201 com id

# 3. Verificar que 4 faturas foram criadas
psql -U postgres casaleconomia_dev \
  -c "SELECT periodo, data_fechamento, data_vencimento, status FROM faturas ORDER BY periodo"
# esperado: 4 linhas (2026-11, 2026-12, 2027-01, 2027-02)

# 4. Criar lançamento vinculado ao cartão
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"descricao\":\"Uber\",\"valor\":\"25.00\",\"data_lancamento\":\"2026-11-09\",\"tipo\":\"despesa\",\"cartao_id\":\"$CARTAO_ID\"}" \
  | python3 -m json.tool
# esperado: 201 com periodo_fatura="2026-11"

# 5. Detalhe da fatura
curl -s http://localhost:8000/faturas/$FATURA_ID -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: valor_total="25.00", status="aberta", 1 lançamento

# 6. Pagar parcialmente
curl -s -X POST http://localhost:8000/faturas/$FATURA_ID/pagar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"valor":"10.00"}' | python3 -m json.tool
# esperado: status="parcialmente_paga"

# 7. Pagar restante
# esperado: status="paga"

# 8. Pagar além do restante → 400

# 9. Arquivar cartão → some da listagem padrão, retorna com incluir_arquivados=true
```

---

## Fora do escopo

- Formulário Angular de criação/edição de cartão (pode ser construído como exercício)
- Histórico de faturas na UI
- Integração do pagamento com conta bancária
- Parcelamento de compras
- Recorrência em cartão
- Ajuste manual do valor da fatura
