# Tarefa 08 — Receitas

## Contexto

Implementa o módulo de criação de receitas do CasalEconomia. Usa a mesma tabela `lancamentos`
(com `tipo = "receita"`), aproveitando toda a infraestrutura de compartilhamento e campos
adicionados na tarefa 07. As diferenças em relação a despesas: sem parcelamento, sem cartão,
sem importação XLSX.

Em compensação, receitas têm o conceito de "previsto vs recebido" mais proeminente e suportam
**recebimento parcial** — você esperava R$ 5.000 de salário mas recebeu R$ 4.500, o restante
fica pendente sem precisar criar um segundo lançamento.

A tela `/lancamentos` também é atualizada para exibir despesas e receitas juntas com filtros
por tipo.

**Pré-requisito:** tarefas 01–07 concluídas.

---

## Melhorias sobre o OpenMonetis

| # | Problema original | Decisão aqui |
|---|---|---|
| 1 | Status "recebido" é só um boolean | Status derivado em 4 estados: `previsto / a_receber / parcialmente_recebido / recebido` |
| 2 | Sem campo "quem paga" | Campo `fonte` — nome da empresa, cliente ou inquilino que originou a receita |
| 3 | Marcar como recebido exige abrir o form completo | Ação rápida "Marcar recebido" direto na lista, sem abrir modal |
| 4 | Sem recebimento parcial | Campo `valor_recebido` — permite registrar quanto de fato entrou na conta |
| 5 | Sem "Salvar e continuar" | Mesmo comportamento da tarefa 07: Seção A limpa, Seção B preservada |

---

## Tabelas: adicionar 2 colunas em `lancamentos` (migration separada)

| Campo novo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `fonte` | VARCHAR(120) | não | Quem originou a receita (empresa, cliente, inquilino); preenchido só para `tipo = "receita"` |
| `valor_recebido` | NUMERIC(12,2) | não | Valor efetivamente recebido; preenchido ao marcar como recebido; permite recebimento parcial |

Nenhuma tabela nova nesta tarefa — toda a estrutura já existe da tarefa 07.

---

## Regras de negócio

### Escopo desta tarefa
Apenas `tipo = "receita"`. Despesas foram na tarefa 07; transferências na tarefa 09.

### Forma de recebimento (campo `forma_pagamento`)

| Valor | Permitido para receita |
|---|---|
| `pix` | sim |
| `transferencia` | sim |
| `dinheiro` | sim |
| `deposito` | sim |
| `outro` | sim |
| `boleto` | **não** (400) |
| `cartao_debito` | **não** (400) |
| `cartao_credito` | **não** (400) |

### Status derivado da receita
Calculado no service a cada leitura; **não persistido** — retornado como campo adicional no response:

```
se liquidado = true  e  valor_recebido < valor  → "parcialmente_recebido"
se liquidado = true                              → "recebido"
se liquidado = false e  data_vencimento > hoje   → "previsto"
senão                                            → "a_receber"
```

O campo `valor_recebido` só é relevante quando `liquidado = true`. Se `liquidado = false`,
`valor_recebido` deve ser nulo.

### Marcar como recebido
Via `PUT /lancamentos/{id}` com body `{ "liquidado": true }` ou `{ "liquidado": true, "valor_recebido": X }`.

- Se `valor_recebido` não informado → `valor_recebido = valor` (recebimento total)
- Se `valor_recebido > valor` → 400 com mensagem "Valor recebido não pode ser superior ao valor esperado"
- Se `valor_recebido <= 0` → 400
- Se `liquidado = false` informado em um `PUT` → zerar `valor_recebido` e `data_liquidacao`

### Sem parcelamento
Campos `total_parcelas`, `serie_id`, `parcela_atual` não são aceitos para `tipo = "receita"`.
Se enviados, retornar 400: "Parcelamento não é suportado para receitas."

Sem `cartao_id` e sem `periodo_fatura` para receitas (mesma regra: 400 se enviados).

### Compartilhamento
Mesmas regras da tarefa 07:
- `email_compartilhado` = e-mail do parceiro conectado (verificado em `conexoes_casal`)
- 400 se o e-mail não pertence a parceiro conectado
- `percentual_compartilhado` = percentual do valor que vai para o parceiro (0–100)
- `valor_compartilhado = valor * percentual_compartilhado / 100` (calculado e persistido)
- Cria registro em `lancamentos_parceiro` para o parceiro aceitar/ignorar

---

## Endpoints

### Já existentes — estender para receitas

**`POST /lancamentos`**
- Aceita `tipo = "receita"` com campos novos: `fonte`, `valor_recebido`
- Rejeita parcelamento, `cartao_id`, `periodo_fatura` para receitas (400)
- Rejeita `forma_pagamento` incompatível (boleto, cartao_debito, cartao_credito)
- Response 201: lançamento criado com `status_receita` calculado

**`GET /lancamentos`**
- Query param `tipo` agora aceita `"receita"`, `"despesa"` ou omitido (retorna todos)
- Cada item de receita inclui `status_receita` calculado no response
- Itens de despesa não incluem `status_receita`

**`PUT /lancamentos/{id}`**
- Aceita `liquidado`, `valor_recebido`, `fonte`
- Response 200 inclui `status_receita` atualizado

**`DELETE /lancamentos/{id}`**
- Mesmo comportamento da tarefa 07

---

## Frontend

### Tela `/lancamentos` — atualizar layout

- Adicionar controle de filtro no topo da lista: **Todos · Despesas · Receitas**
- Itens de receita na lista exibem:
  - Descrição, valor formatado como moeda
  - `fonte` abaixo da descrição (se preenchida), em texto secundário
  - Chip de status com cor:
    - `previsto` → azul claro (`--color-cyan`)
    - `a_receber` → amarelo (`#f59e0b`)
    - `parcialmente_recebido` → laranja (`#f97316`)
    - `recebido` → verde (`#22c55e`)
  - Data prevista ("Prevista para 05/12") quando `data_vencimento` preenchida
  - **Botão de check** (ícone círculo vazio): visível ao lado de itens com status `previsto`
    ou `a_receber` → clique chama `PUT /lancamentos/{id}` com `{ liquidado: true }` →
    item muda para `recebido` sem abrir modal
- FAB "+" expande com dois botões: "Despesa" e "Receita"
- Botão "Importar lançamentos" permanece visível (continua abrindo `ModalImportarDespesasComponent`)

### `ModalCriarReceitaComponent` (modal de criação)

**Seção A — limpa ao clicar em "Salvar e continuar":**
- `descricao` (texto, obrigatório, máx 200)
- `data_lancamento` (date, obrigatório, default hoje)
- `valor` (decimal positivo, obrigatório)

**Seção B — preservada ao "Salvar e continuar":**
- `forma_recebimento` (select com rótulos PT-BR: Pix, Transferência, Dinheiro, Depósito, Outro)
- `conta_id` (select desabilitado com texto "Conta — disponível em breve"; opcional)
- Toggle "Status": **A receber** / **Recebido** (default "A receber")
- `valor_recebido` (decimal; visível apenas quando toggle = "Recebido"; default igual a `valor`;
  ao diminuir o valor, preview mostra "Recebimento parcial — faltam R$ X")
- `data_vencimento` (date; label: "Data prevista de recebimento"; opcional)
- `fonte` (input texto; label: "Origem / Fonte"; placeholder: "Ex.: Empresa XYZ, Inquilino João"; opcional)
- `categoria` (input texto; opcional)
- `nota` (textarea; opcional)
- **Seção Compartilhamento** (exibida apenas se usuário tiver parceiro conectado):
  - Checkbox "Compartilhar com [Nome do Parceiro]"
  - `percentual_compartilhado` (0–100, default 50; visível se checkbox marcado)
  - Preview: "Parceiro recebe: R$ X,XX"

**Botões:** Cancelar | **Salvar e continuar** | **Salvar**

Comportamento de "Salvar e continuar": submete o formulário e, se bem-sucedido, limpa apenas os
campos da Seção A, mantém foco em `descricao`, mantém o modal aberto.

### `LancamentosService` (atualizar métodos existentes)

Adicionar ao serviço já criado na tarefa 07:
- `criarReceita(dados)` → chama `POST /lancamentos` com `tipo = "receita"` fixo
- `marcarRecebido(id: string, valorRecebido?: number)` → chama `PUT /lancamentos/{id}` com
  `{ liquidado: true, valor_recebido: valorRecebido }` (valor omitido = recebimento total)

---

## Verificação

```bash
# 1. Novas colunas
psql -U postgres casaleconomia_dev -c "\d lancamentos"
# esperado: colunas fonte e valor_recebido presentes

# 2. Criar receita "a receber"
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Salário novembro","valor":"5000.00","data_lancamento":"2026-11-05","tipo":"receita","forma_pagamento":"transferencia","fonte":"Empresa ABC","data_vencimento":"2026-11-05"}' \
  | python3 -m json.tool
# esperado: 201, liquidado=false, status_receita="a_receber"

# 3. Criar receita "prevista" (vencimento futuro)
# data_vencimento="2026-12-05" (além de hoje)
# esperado: status_receita="previsto"

# 4. Marcar como recebido (total)
curl -s -X PUT http://localhost:8000/lancamentos/$ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"liquidado":true}' | python3 -m json.tool
# esperado: liquidado=true, valor_recebido=5000.00, status_receita="recebido"

# 5. Marcar recebimento parcial
curl -s -X PUT http://localhost:8000/lancamentos/$ID2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"liquidado":true,"valor_recebido":"1800.00"}' | python3 -m json.tool
# esperado: status_receita="parcialmente_recebido", valor_recebido=1800.00

# 6. Rejeitar parcelamento em receita
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Aluguel","valor":"1500.00","data_lancamento":"2026-11-01","tipo":"receita","forma_pagamento":"pix","total_parcelas":3}' \
  | python3 -m json.tool
# esperado: 400 com mensagem em PT-BR

# 7. Rejeitar forma de pagamento incompatível
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Teste","valor":"100.00","data_lancamento":"2026-11-01","tipo":"receita","forma_pagamento":"boleto"}' \
  | python3 -m json.tool
# esperado: 400

# 8. valor_recebido maior que valor → 400
curl -s -X PUT http://localhost:8000/lancamentos/$ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"liquidado":true,"valor_recebido":"99999.00"}' | python3 -m json.tool
# esperado: 400

# 9. Listar somente receitas do mês
curl -s "http://localhost:8000/lancamentos?tipo=receita&mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: somente itens com tipo=receita, cada um com status_receita

# 10. Listar somente despesas (sem status_receita)
curl -s "http://localhost:8000/lancamentos?tipo=despesa&mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: somente itens com tipo=despesa, sem campo status_receita

# 11. Receita compartilhada 50%
# esperado: lancamentos_parceiro criado com valor_compartilhado = valor * 0.5
```

Frontend:
- Abrir `/lancamentos` → ver filtros Todos / Despesas / Receitas
- Clicar em "+" → submenu com "Despesa" e "Receita"
- Criar receita prevista → aparece com chip "Previsto" azul
- Clicar no botão de check → chip muda para "Recebido" verde sem abrir modal
- Criar receita → "Salvar e continuar" → Seção A limpa, Seção B mantida com forma de recebimento

---

## Fora do escopo

- Receitas recorrentes (tarefa 10)
- Integração com contas bancárias (`conta_id` aceito no body mas não validado até tarefa 09)
- Categorias tabularizadas com ícones e cores (tarefa futura)
- Importação XLSX de receitas
- Cobranças / contas a receber com juros e multa
- Relatórios de receita vs despesa
- Desfazer marcação de recebimento parcial e criar novo lançamento para o saldo restante
