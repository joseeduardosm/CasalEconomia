# Tarefa 07 — Despesas

## Contexto

Implementa o módulo completo de criação de despesas do CasalEconomia. O usuário pode registrar
despesas avulsas, parceladas no cartão ou boleto, e compartilhar o custo com o parceiro informando
apenas o percentual. Inclui o fluxo "Salvar e continuar" para lançamento em série e importação de
extrato de cartão via planilha XLSX.

Baseado no fluxo de lançamentos do OpenMonetis, com cinco melhorias estruturais descritas abaixo.
Recorrências são escopo da tarefa 10 — esta tarefa cobre apenas despesas avulsas e parceladas.

**Pré-requisito:** tarefas 01–06 concluídas. A tabela `lancamentos` já existe com `cartao_id` e
`periodo_fatura`; `lancamentos_parceiro` e o sincronizador já existem.

---

## Melhorias sobre o OpenMonetis

| # | Problema original | Decisão aqui |
|---|---|---|
| 1 | Split requer valores explícitos por pessoa | Modo "compartilhamento %" — usuário informa só o percentual do parceiro; valor calculado |
| 2 | Sem "Salvar e continuar" | Botão mantém modal aberto, limpa somente os campos temporários |
| 3 | Sem importação XLSX nativa para cartão | Modal com "Baixar modelo" + validação visual antes de confirmar |
| 4 | `startInstallment` confuso para o usuário | Campo "A partir da parcela Nº" com tooltip explicativo no form |
| 5 | Recorrência não pode ter valor variável | Flag `valor_aproximado` boolean — sinaliza que o valor pode mudar mês a mês (preparatório para tarefa 10) |

---

## Tabelas

### `series_parcelamento` (nova)

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `total_parcelas` | SMALLINT | sim | Total original da série (2–60) |
| `parcela_inicio` | SMALLINT | sim | A partir de qual parcela foi rastreada (default 1) |
| `valor_total` | NUMERIC(12,2) | sim | Valor total da compra (soma de todas as parcelas) |
| `criado_em` | TIMESTAMPTZ | sim | |

### `lancamentos` — adicionar colunas (migration separada)

| Campo novo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `forma_pagamento` | VARCHAR(30) | não | `dinheiro/pix/boleto/cartao_debito/cartao_credito/transferencia` |
| `conta_id` | UUID FK → `contas.id` SET NULL | não | Reservado para tarefa 08; aceitar na criação sem validar existência |
| `liquidado` | BOOLEAN | não | `null` = cartao_credito; `false` = pendente; `true` = pago |
| `data_vencimento` | DATE | não | Data de vencimento da despesa |
| `data_liquidacao` | DATE | não | Data em que foi pago de fato |
| `nota` | VARCHAR(1000) | não | Observação livre |
| `serie_id` | UUID FK → `series_parcelamento.id` SET NULL | não | Liga parcelas da mesma série |
| `parcela_atual` | SMALLINT | não | Número desta parcela (1-based) |
| `email_compartilhado` | VARCHAR(255) | não | E-mail do parceiro que receberá cópia |
| `percentual_compartilhado` | NUMERIC(5,2) | não | Percentual do valor que vai para o parceiro (0–100) |
| `valor_compartilhado` | NUMERIC(12,2) | não | Calculado: `valor * percentual / 100`, persistido |
| `categoria` | VARCHAR(80) | não | Categoria livre por texto (categorias tabularizadas são tarefa futura) |
| `valor_aproximado` | BOOLEAN | não | default `false`; preparatório para recorrências com valor variável (tarefa 10) |

---

## Regras de negócio

### Escopo desta tarefa
Apenas `tipo = "despesa"`. Receitas são tarefa 08; transferências são tarefa 09.

### Forma de pagamento vs campos obrigatórios

| `forma_pagamento` | `cartao_id` | `liquidado` padrão | Parcelamento permitido |
|---|---|---|---|
| `cartao_credito` | obrigatório | `null` | sim |
| `boleto` | — | `false` | sim |
| `dinheiro`, `pix`, `cartao_debito`, `transferencia` | — | `false` | não |

- `conta_id` é aceito em qualquer forma de pagamento, mas não é validado até a tarefa 08.
- Se `forma_pagamento` não informado → armazenar `null` (campo legado de lançamentos da tarefa 05).

### Parcelamento

- Apenas para `cartao_credito` ou `boleto`
- `total_parcelas` entre 2 e 60
- `parcela_inicio` entre 1 e `total_parcelas` (default 1; valor maior = importar compra já iniciada)
- Distribuição de centavos: o valor por parcela é `valor / total_parcelas` arredondado para baixo;
  o centavo residual é adicionado às primeiras parcelas, uma a uma, para garantir que a soma bata exatamente
- Cria registro em `series_parcelamento` antes de inserir as parcelas
- Cada parcela recebe `serie_id`, `parcela_atual` (início em `parcela_inicio`), `periodo_fatura`
  calculado individualmente (parcela N = periodo da parcela 1 + N-1 meses)
- Apenas as parcelas a partir de `parcela_inicio` são criadas (parcelas anteriores existem no
  cartão físico mas não no sistema)

### Derivação de `periodo_fatura` (para cartão de crédito)

1. Se `periodo_fatura` informado explicitamente → usar diretamente
2. Senão, buscar a fatura do mês atual para o cartão:
   - Se `data_lancamento > data_fechamento` da fatura do mês atual → `periodo_fatura` = mês seguinte
   - Caso contrário → `periodo_fatura` = mês atual

### Compartilhamento

- `email_compartilhado` deve pertencer ao parceiro conectado ao usuário autenticado
  (verificado via `conexoes_casal` → lookup de `users.email`)
- 400 se o e-mail não pertence a um parceiro conectado
- Se informado, o service cria registros em `lancamentos_parceiro` para o parceiro aceitar:
  - Lançamento avulso: 1 registro de `lancamentos_parceiro`
  - Lançamento parcelado: 1 registro por parcela, cada um com o `valor_compartilhado` correspondente
- `valor_compartilhado = valor_parcela * percentual_compartilhado / 100` (calculado e persistido)
- O sincronizador existente (tarefa 05) se encarrega de notificar o parceiro

### Exclusão

- Lançamento avulso: delete físico do registro
- Parcela de série (sem query param): delete físico somente daquela parcela
- Parcela de série com `?escopo=serie`: delete físico de todas as parcelas da série com
  `parcela_atual >= parcela_atual do lançamento excluído` — parcelas anteriores (já pagas) são preservadas
- Ao excluir qualquer lançamento que tenha `lancamentos_parceiro` associados: deletar os
  `lancamentos_parceiro` correspondentes e os `lancamentos` importados pelo parceiro
  (mesma lógica de exclusão propagada já descrita na tarefa 05)

### Importação XLSX

Dependência nova: `openpyxl==3.1.5` — adicionar ao `requirements.txt`

**Colunas esperadas (posição fixa, header case-insensitive):**

| Col | Nome | Obrigatório | Validações |
|---|---|---|---|
| A | Descrição | sim | 1–200 chars |
| B | Data (AAAA-MM-DD) | sim | formato ISO, não pode ser futura além de 1 ano |
| C | Valor por Parcela | sim | decimal positivo, máx 999999.99 |
| D | Parcela Atual | não | inteiro 1–60 |
| E | Total de Parcelas | não | inteiro 2–60; obrigatório se D preenchido; deve ser >= D |
| F | Categoria | não | texto livre, máx 80 chars |
| G | Email Compartilhado | não | e-mail válido; parceiro deve estar conectado ao usuário |
| H | % Compartilhamento | não | 0–100; obrigatório se G preenchido |

**Caso especial:** se D e E vazios mas G e H preenchidos → G é o e-mail de compartilhamento e
H é o percentual. O usuário pode omitir as colunas de parcelamento e preencher as de compartilhamento.

**Fluxo em dois passos:**
1. `POST /lancamentos/importar` — recebe arquivo, valida todas as linhas, **não persiste nada**,
   retorna `{ linhas_validas: [...], linhas_com_erro: [...] }` onde erros têm `linha` e `problema`
2. `POST /lancamentos/importar/confirmar` — recebe o array `linhas` (igual ao `linhas_validas`
   retornado no passo 1) e persiste somente esses registros

Erros em linhas não bloqueiam a confirmação das linhas válidas.

---

## Endpoints

### Já existentes (tarefa 05) — estender para incluir campos novos

**`POST /lancamentos`**
- Autenticação: obrigatória
- Body: campos existentes + todos os campos novos opcionais
- Lógica nova: criação de série de parcelamento, derivação de `periodo_fatura`, compartilhamento
- Response 201: lançamento criado (ou primeira parcela, se parcelado)

**`GET /lancamentos`**
- Autenticação: obrigatória
- Query params novos: `mes` (YYYY-MM, default mês atual), `cartao_id`, `liquidado` (true/false)
- Response 200: lista com todos os campos novos incluídos

### Novos

**`PUT /lancamentos/{id}`**
- Autenticação: obrigatória
- Body: campos editáveis (todos opcionais no body)
- Query param: `escopo=serie` → aplica alterações de `descricao`, `categoria`, `nota` a todas as
  parcelas da mesma `serie_id`; demais campos são editados só no lançamento individual
- Response 200: lançamento atualizado
- Erros: 404 se não encontrado, 403 se não pertence ao usuário

**`DELETE /lancamentos/{id}`**
- Autenticação: obrigatória
- Query param: `escopo=serie` → exclui série a partir desta parcela (ver regra acima)
- Response 200: `{ mensagem: "Lançamento excluído." }` ou `{ mensagem: "X parcelas excluídas." }`
- Erros: 404, 403

**`GET /lancamentos/modelo-importacao`**
- Autenticação: obrigatória
- Response 200: arquivo XLSX para download
- Header: `Content-Disposition: attachment; filename="modelo-lancamentos.xlsx"`
- Conteúdo: linha de cabeçalho com as 8 colunas + 3 linhas de exemplo comentadas (1 avulsa, 1
  parcelada, 1 compartilhada)

**`POST /lancamentos/importar`**
- Autenticação: obrigatória
- Body: `multipart/form-data` com campo `arquivo` (.xlsx)
- Response 200: `{ linhas_validas: [...], linhas_com_erro: [...] }`
- Cada linha válida: objeto com todos os campos já normalizados
- Cada linha com erro: `{ numero_linha: int, problema: "mensagem em PT-BR" }`

**`POST /lancamentos/importar/confirmar`**
- Autenticação: obrigatória
- Body: `{ linhas: [...] }` (array normalizado retornado pelo endpoint anterior)
- Response 201: `{ criados: int }`

---

## Dependências Python a adicionar

`openpyxl==3.1.5` ao `requirements.txt`

---

## Frontend

### Tela `/lancamentos` (substituir placeholder da tarefa 03)

- Lista de despesas do mês ativo (período vindo do `BarraTopoComponent`)
- Agrupada por data, mais recente primeiro
- Cada item exibe: descrição, valor (formatado como moeda), ícone da forma de pagamento, chip de
  status (Pago / Pendente / Cartão), indicador de parcela ("2/6") se aplicável, ícone de
  compartilhado se `email_compartilhado` preenchido
- Swipe para a esquerda no item (mobile) ou botão "Excluir" (desktop) → confirmar antes de excluir
- Botão flutuante "+" no canto inferior direito → abre `ModalCriarDespesaComponent`
- Botão "Importar lançamentos" na barra superior → abre `ModalImportarDespesasComponent`

### `ModalCriarDespesaComponent` (modal de criação)

**Seção A — limpa ao clicar em "Salvar e continuar":**
- `descricao` (texto, obrigatório, máx 200)
- `data_lancamento` (date, obrigatório, default hoje)
- `valor` (decimal positivo, obrigatório)
- Toggle "Parcelado" (visível apenas se `forma_pagamento` = `cartao_credito` ou `boleto`)
- `total_parcelas` (2–60, visível se toggle ativo)
- `parcela_inicio` (1–total_parcelas, visível se toggle ativo; tooltip: "Preencha com um número
  maior que 1 se você está importando uma compra já iniciada")

**Seção B — preservada ao "Salvar e continuar":**
- `forma_pagamento` (select com rótulos PT-BR: Dinheiro, Pix, Boleto, Cartão Débito, Cartão
  Crédito, Transferência)
- `cartao_id` (select com lista de cartões ativos do usuário; visível apenas se `cartao_credito`)
- `periodo_fatura` (select de período YYYY-MM; visível apenas se `cartao_credito`; valor padrão
  calculado pelo backend; campo opcional — deixar em branco usa o cálculo automático)
- `liquidado` (toggle Sim/Não, default Não; oculto se `cartao_credito`)
- `data_vencimento` (date; opcional)
- `categoria` (input texto; opcional)
- `nota` (textarea; opcional)
- **Seção Compartilhamento** (exibida apenas se o usuário tiver parceiro conectado):
  - Checkbox "Compartilhar com [Nome do Parceiro]"
  - `percentual_compartilhado` (input numérico 0–100, default 50; visível se checkbox marcado)
  - Preview dinâmico: "Parceiro paga: R$ X,XX" (calculado em tempo real)

**Botões na base do modal:**
Cancelar | **Salvar e continuar** | **Salvar**

Comportamento de "Salvar e continuar": submete o formulário, e se bem-sucedido limpa apenas os
campos da Seção A, mantém foco em `descricao`, mantém o modal aberto.

### `ModalImportarDespesasComponent` (modal de importação — 2 etapas)

**Etapa 1 — Seleção:**
- Título: "Importar lançamentos do cartão"
- Botão "Baixar modelo" → `GET /lancamentos/modelo-importacao` → download automático
- Área de upload: dropzone com texto "Arraste o arquivo .xlsx ou clique para selecionar"
- Aceita apenas `.xlsx`; ao selecionar: spinner + chama `POST /lancamentos/importar` → avança para etapa 2

**Etapa 2 — Validação:**
- Título: "Revise os lançamentos"
- Contador: "X lançamentos válidos · Y com problema"
- Tabela com todas as linhas: Nº, Descrição, Data, Valor, Parcela, Categoria, Compartilhamento, Problema
- Linhas com erro: fundo `rgba(239,68,68,0.06)`, coluna "Problema" em vermelho com mensagem PT-BR
- Linhas válidas: normais
- Erros não bloqueiam o botão de confirmar (somente linhas válidas serão importadas)
- Botão "Confirmar X lançamentos" → `POST /lancamentos/importar/confirmar` → fecha modal, recarrega lista
- Botão "Voltar" → retorna à etapa 1
- Botão "Cancelar" → fecha modal sem importar

### `LancamentosService` (Angular, singleton, `providedIn: 'root'`)

Métodos:
- `listar(filtros: { mes?: string; cartao_id?: string; liquidado?: boolean })` → Observable
- `criar(dados)` → Observable
- `atualizar(id: string, dados, escopo?: 'individual' | 'serie')` → Observable
- `excluir(id: string, escopo?: 'individual' | 'serie')` → Observable
- `baixarModelo()` → dispara download do arquivo XLSX
- `validarImportacao(arquivo: File)` → Observable com `{ linhas_validas, linhas_com_erro }`
- `confirmarImportacao(linhas: any[])` → Observable com `{ criados: number }`

---

## Verificação

```bash
# 1. Tabelas
psql -U postgres casaleconomia_dev -c "\d lancamentos"
# esperado: colunas forma_pagamento, liquidado, nota, serie_id, parcela_atual,
#           email_compartilhado, percentual_compartilhado, valor_compartilhado, categoria

psql -U postgres casaleconomia_dev -c "\dt series_parcelamento"
# esperado: tabela existe

# 2. Despesa avulsa simples (Pix)
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Almoço","valor":"45.00","data_lancamento":"2026-11-09","tipo":"despesa","forma_pagamento":"pix"}' \
  | python3 -m json.tool
# esperado: 201, liquidado=false, serie_id=null

# 3. Despesa parcelada no cartão (3x de R$ 100)
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"descricao\":\"TV\",\"valor\":\"100.00\",\"data_lancamento\":\"2026-11-09\",\"tipo\":\"despesa\",\"forma_pagamento\":\"cartao_credito\",\"cartao_id\":\"$CARTAO_ID\",\"parcelado\":true,\"total_parcelas\":3}" \
  | python3 -m json.tool
# esperado: 201; verificar no banco: 3 linhas com mesmo serie_id, parcela_atual 1,2,3

psql -U postgres casaleconomia_dev \
  -c "SELECT parcela_atual, valor, periodo_fatura FROM lancamentos WHERE serie_id IS NOT NULL ORDER BY parcela_atual"
# esperado: 3 linhas com valores iguais (ou diferença de 1 centavo), periodos incrementados

# 4. Despesa compartilhada 50%
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Jantar","valor":"200.00","data_lancamento":"2026-11-09","tipo":"despesa","forma_pagamento":"pix","email_compartilhado":"parceiro@teste.com","percentual_compartilhado":50}' \
  | python3 -m json.tool
# esperado: 201, valor_compartilhado=100.00; registro criado em lancamentos_parceiro

psql -U postgres casaleconomia_dev -c "SELECT * FROM lancamentos_parceiro ORDER BY criado_em DESC LIMIT 1"
# esperado: linha com snapshot do lançamento compartilhado

# 5. Download do modelo XLSX
curl -s -o /tmp/modelo.xlsx http://localhost:8000/lancamentos/modelo-importacao \
  -H "Authorization: Bearer $TOKEN"
file /tmp/modelo.xlsx
# esperado: Microsoft XLSX spreadsheet

# 6. Validar importação (sem persistir)
curl -s -X POST http://localhost:8000/lancamentos/importar \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@/home/administrador/casalEconomia/apoio/importacao_fatura_9503_nov2026.xlsx" \
  | python3 -m json.tool
# esperado: linhas_validas (N linhas), linhas_com_erro (M linhas com problema)
# verificar que nenhum lançamento novo aparece no banco ainda

# 7. Confirmar importação
# pegar as linhas_validas do passo anterior como corpo e confirmar
# esperado: { "criados": N }

psql -U postgres casaleconomia_dev -c "SELECT COUNT(*) FROM lancamentos WHERE usuario_id = '$USER_ID'"
# esperado: contagem aumentou em N

# 8. Excluir série
curl -s -X DELETE "http://localhost:8000/lancamentos/$LANCAMENTO_ID?escopo=serie" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: mensagem com número de parcelas excluídas; parcelas anteriores preservadas

# 9. Atualizar lançamento individual vs série
curl -s -X PUT "http://localhost:8000/lancamentos/$LANCAMENTO_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"TV 4K"}' | python3 -m json.tool
# esperado: somente este lançamento alterado

curl -s -X PUT "http://localhost:8000/lancamentos/$LANCAMENTO_ID?escopo=serie" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"categoria":"Eletrônicos"}' | python3 -m json.tool
# esperado: categoria atualizada em todas as parcelas da série
```

Frontend:
- Abrir `/lancamentos` → lista do mês atual
- Clicar em "+" → modal abre com `descricao` em foco
- Preencher campos → "Salvar e continuar" → modal fica aberto, Seção A limpa, Seção B mantida
- Clicar em "Importar lançamentos" → modal de importação → baixar modelo → selecionar planilha →
  ver tabela de validação → confirmar → lista recarrega com lançamentos importados

---

## Fora do escopo

- Receitas (tarefa 08)
- Transferências entre contas (tarefa 09)
- Recorrências (tarefa 10)
- Categorias tabularizadas com ícones e cores (tarefa futura)
- Contas bancárias (`conta_id` é aceito mas não validado até tarefa 08)
- Importação de arquivo OFX/QIF
- Reembolso parcial de despesa
- Edição de lançamento compartilhado já aceito pelo parceiro
- Relatórios e gráficos de despesas
