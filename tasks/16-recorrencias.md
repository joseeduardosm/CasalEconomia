# Tarefa 16 — Lançamentos Recorrentes

## Contexto

Implementa o módulo de recorrências: lançamentos que se repetem automaticamente em uma frequência
definida (semanal, mensal, anual, etc.). Elimina a necessidade de criar manualmente o mesmo
lançamento a cada período — aluguel, salário, assinaturas, mensalidades.

A recorrência é uma **regra**, não uma lista de lançamentos materializados. O sincronizador
(tarefa 05) é responsável por gerar as ocorrências em `lancamentos` conforme o tempo avança.
Ao consultar o relatório de recorrentes (tarefa 12 R5), os dados já estarão disponíveis.

**Pré-requisito:** tarefas 01–15 concluídas.

---

## Conceito central

Uma recorrência define QUANDO e QUANTO um lançamento deve ocorrer. Cada execução do sincronizador
verifica quais recorrências têm ocorrências a gerar no período atual e as cria em `lancamentos`
com `recorrencia_id` vinculado. O saldo das contas e o painel refletem as ocorrências materializadas.

### Diferença de parcelamento vs recorrência

| Parcelamento (`series_parcelamento`) | Recorrência (`regras_recorrencia`) |
|---|---|
| Número fixo de parcelas | Sem fim definido (ou com `data_fim`) |
| Valor total repartido entre parcelas | Valor fixo por ocorrência |
| Termina automaticamente | Precisa ser cancelada ou ter `data_fim` |
| Ex: celular em 12x | Ex: Netflix mensal, aluguel, salário |

---

## Novas tabelas

### `regras_recorrencia`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `descricao` | VARCHAR(200) | sim | ex: "Aluguel", "Netflix" |
| `tipo` | VARCHAR(10) | sim | `receita` / `despesa` |
| `valor` | NUMERIC(12,2) | sim | valor por ocorrência |
| `forma_pagamento` | VARCHAR(30) | sim | igual a `lancamentos` |
| `cartao_id` | UUID FK → `cartoes.id` | não | se pago em cartão |
| `conta_id` | UUID FK → `contas.id` | não | conta de débito |
| `categoria` | VARCHAR(80) | não | |
| `nota` | VARCHAR(500) | não | |
| `frequencia` | VARCHAR(20) | sim | `semanal` / `quinzenal` / `mensal` / `bimestral` / `trimestral` / `semestral` / `anual` |
| `dia_do_mes` | SMALLINT | não | 1–31; se `frequencia` = mensal/bimestral/etc. |
| `dia_da_semana` | SMALLINT | não | 0=dom … 6=sab; se `frequencia` = semanal |
| `data_inicio` | DATE | sim | primeira ocorrência |
| `data_fim` | DATE | não | última ocorrência permitida (inclusivo) |
| `status` | VARCHAR(20) | sim | `ativa` / `pausada` / `cancelada` |
| `ultima_geracao` | DATE | não | última data em que o sincronizador gerou ocorrência |
| `criado_em` | TIMESTAMPTZ | sim | |
| `atualizado_em` | TIMESTAMPTZ | sim | |

### Coluna nova em `lancamentos`

| Campo | Tipo | Notas |
|---|---|---|
| `recorrencia_id` | UUID FK → `regras_recorrencia.id` | nulo para lançamentos avulsos |

---

## Regras de negócio

### Geração de ocorrências pelo sincronizador

O sincronizador (APScheduler, 60s) executa a rotina de recorrências:

1. Busca todas as `regras_recorrencia` com `status = "ativa"`
2. Para cada regra, calcula a próxima data após `ultima_geracao` (ou `data_inicio` se nunca gerou)
3. Se a próxima data for ≤ hoje E ≤ `data_fim` (se houver): cria o lançamento em `lancamentos`
   com `recorrencia_id`, `liquidado = false`, e demais campos copiados da regra
4. Atualiza `ultima_geracao` da regra para a data gerada
5. Repete até que a próxima data ultrapasse hoje ou `data_fim`

**Idempotência:** antes de criar, verificar se já existe `lancamento` com mesmo `recorrencia_id`
e `data_lancamento` igual à data calculada. Se sim, pular (evitar duplicata em caso de reinício
do sincronizador).

### Cálculo de próxima data

Dada a `ultima_geracao` ou `data_inicio`, a próxima data é calculada somando o intervalo da
frequência. Para `mensal` com `dia_do_mes = 15`: próximo mês no dia 15 (se o mês não tem esse
dia, usar o último dia do mês). Para `semanal` com `dia_da_semana = 5` (sex): próxima sexta-feira.

### Edição de recorrência

- Editar uma recorrência **não altera** lançamentos já criados no passado
- Alterações valem apenas para ocorrências futuras
- Se `valor`, `categoria` ou `forma_pagamento` mudar, o próximo lançamento gerado reflete o novo valor
- Cancelar uma recorrência (`status = "cancelada"`) para definitivamente; não gerou novas ocorrências
- Pausar (`status = "pausada"`) suspende temporariamente sem apagar o histórico

### Exclusão de ocorrência avulsa

O usuário pode deletar um lançamento individual que veio de uma recorrência. Isso exclui apenas
aquela ocorrência — a regra continua gerando as próximas. É o mecanismo para "pular um mês".

---

## Endpoints

### `POST /recorrencias`
- Autenticação: obrigatória
- Body: `descricao`, `tipo`, `valor`, `forma_pagamento`, `cartao_id` (opt), `conta_id` (opt),
  `categoria` (opt), `nota` (opt), `frequencia`, `dia_do_mes` (opt), `dia_da_semana` (opt),
  `data_inicio`, `data_fim` (opt)
- Response 201: regra criada; o sincronizador gerará a primeira ocorrência na próxima rodada

### `GET /recorrencias`
- Autenticação: obrigatória
- Query params: `status` (ativa/pausada/cancelada/todos — default `ativa`), `tipo` (receita/despesa/todos)
- Response 200: lista de regras com `proxima_ocorrencia: DATE` calculada

### `GET /recorrencias/{id}`
- Autenticação: obrigatória
- Response 200: regra com histórico das últimas 12 ocorrências em `lancamentos`

### `PUT /recorrencias/{id}`
- Autenticação: obrigatória — somente o dono
- Body: campos editáveis (descricao, valor, categoria, nota, forma_pagamento, data_fim, dia_do_mes)
- Response 200: regra atualizada

### `PATCH /recorrencias/{id}/status`
- Autenticação: obrigatória — somente o dono
- Body: `status` (`ativa` / `pausada` / `cancelada`)
- Response 200: status atualizado

### `DELETE /recorrencias/{id}`
- Autenticação: obrigatória — somente o dono
- Apenas regras com `status = "cancelada"` podem ser deletadas definitivamente
- Response 200: regra removida (lançamentos vinculados permanecem)

---

## Integração com relatório R3 (Compromissos — tarefa 12)

O endpoint `GET /relatorios/compromissos` atualmente retorna `recorrencias_total: 0` com nota
"tarefa futura". Com esta tarefa implementada, a lógica deve projetar as ocorrências futuras
das recorrências ativas para os próximos N meses e incluí-las no total comprometido.

---

## Integração com relatório R5 (tarefa 12)

`GET /relatorios/recorrentes` passa a retornar dados reais de `regras_recorrencia` com
`total_gerado_no_ano` calculado como soma dos lançamentos vinculados no ano corrente.

---

## Frontend

### Entrada no modal de despesa/receita (tarefas 07/08)

Adicionar seção "Repetição" (colapsável) no `ModalCriarDespesaComponent` e `ModalCriarReceitaComponent`:
- Toggle "Este lançamento se repete?"
- Se ativado: seletor de `frequencia`, campo `data_fim` (opcional)
- Ao salvar com repetição ativa: chama `POST /recorrencias` em vez de `POST /lancamentos`

### Tela `/recorrencias` (nova rota)

- Lista de cards de recorrências ativas
- Cada card: ícone de pagamento, descrição, valor, frequência, próxima ocorrência, status
- Filtro rápido: Ativas / Pausadas / Todas
- Botão "Pausar" / "Reativar" / "Cancelar" em cada card
- Clicar no card → tela de detalhe `/recorrencias/:id`

### Tela detalhe `/recorrencias/:id`

- Dados da regra (editável via botão "Editar")
- Próxima ocorrência prevista
- Histórico de ocorrências (`TabelaLancamentosComponent`) com as últimas 12 geradas
- Botões: Editar regra, Pausar/Retomar, Cancelar regra

### `RecorrenciasService` (Angular, singleton)

Métodos: `listar(filtros)`, `criar(dados)`, `atualizar(id, dados)`, `alterarStatus(id, status)`,
`detalhe(id)`, `excluir(id)`

---

## Verificação

```bash
# 1. Criar recorrência mensal
curl -s -X POST http://localhost:8000/recorrencias \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"descricao":"Aluguel","tipo":"despesa","valor":"1500.00","forma_pagamento":"transferencia","frequencia":"mensal","dia_do_mes":5,"data_inicio":"2026-11-05"}' \
  | python3 -m json.tool
# esperado: 201 com id e proxima_ocorrencia

# 2. Aguardar sincronizador (ou acionar manualmente) → verificar lançamento criado
curl -s "http://localhost:8000/lancamentos?mes=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lançamento com recorrencia_id preenchido

# 3. Listar recorrências
curl -s http://localhost:8000/recorrencias \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lista com proxima_ocorrencia calculada

# 4. Pausar recorrência
curl -s -X PATCH http://localhost:8000/recorrencias/$ID/status \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"pausada"}' | python3 -m json.tool
# esperado: status=pausada; sincronizador não gera mais ocorrências

# 5. Reativar
# PATCH status=ativa → ocorrências voltam a ser geradas

# 6. Deletar ocorrência avulsa → regra continua; próxima ocorrência do mês seguinte é gerada

# 7. Relatório R3 agora inclui recorrencias_total para os próximos meses
curl -s "http://localhost:8000/relatorios/compromissos?meses_futuros=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: recorrencias_total > 0 se há recorrências ativas
```

Frontend:
- Criar recorrência mensal → aparece na lista `/recorrencias`
- Aguardar sincronizador → lançamento aparece em `/lancamentos` com indicador "recorrente"
- Pausar → próximo mês sem lançamento gerado
- Cancelar → não aparecem mais ocorrências; histórico permanece

---

## Fora do escopo

- Recorrências compartilhadas com o parceiro
- Edição em lote de ocorrências passadas ao alterar regra
- "Pular" uma ocorrência sem deletar o lançamento
- Recorrência com valor variável (indexada a inflação, etc.)
- Recorrência semanal com múltiplos dias da semana
- Notificação antes de ocorrência gerada
