# Tarefa 05 — Sincronizador de Lançamentos do Casal

## Contexto

Permite que os lançamentos financeiros de um usuário sejam compartilhados automaticamente com o
parceiro conectado. Um job em background (o "sincronizador") roda a cada 60 segundos, detecta
novos lançamentos próprios de usuários com parceiro e cria registros de pendência. O parceiro pode
aceitar (o lançamento entra na carteira dele) ou ignorar.

Baseado no padrão `external_expenses` do OpenMonetis — um registro de sincronização com snapshot
dos dados e trava de concorrência otimista.

**Pré-requisito:** tarefas 01 a 04 concluídas (em especial a tabela `conexoes_casal`).

---

## Tabelas a criar

### `lancamentos`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `descricao` | VARCHAR(200) | sim | |
| `valor` | NUMERIC(12,2) | sim | positivo |
| `data_lancamento` | DATE | sim | |
| `tipo` | VARCHAR(10) | sim | `"receita"` ou `"despesa"` |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | |
| `origem` | VARCHAR(20) | sim | `"proprio"` ou `"compartilhado"` |
| `lancamento_origem_id` | UUID FK → `lancamentos.id` SET NULL | não | aponta ao original quando `compartilhado` |
| `criado_em` | TIMESTAMPTZ | sim | |

> **Nota:** esta tarefa cria o modelo mínimo. Os campos `cartao_id` e `periodo_fatura` serão adicionados na tarefa 06.

### `lancamentos_parceiro`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `lancamento_id` | UUID FK → `lancamentos.id` CASCADE | sim | índice |
| `usuario_dono_id` | UUID FK → `users.id` CASCADE | sim | quem criou o original |
| `usuario_parceiro_id` | UUID FK → `users.id` CASCADE | sim | quem precisa aceitar; índice |
| `status` | VARCHAR(20) | sim | `"pendente"` / `"aceito"` / `"ignorado"` |
| `versao_fonte` | INTEGER | sim | default 0; trava otimista |
| `lancamento_importado_id` | UUID | não | ID do lançamento criado ao aceitar |
| `snapshot_descricao` | VARCHAR(200) | sim | cópia dos dados no momento da sync |
| `snapshot_valor` | NUMERIC(12,2) | sim | |
| `snapshot_data` | DATE | sim | |
| `snapshot_tipo` | VARCHAR(10) | sim | |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Endpoints

### `POST /lancamentos`
- Autenticação: obrigatória
- Body: `descricao`, `valor` (string decimal), `data_lancamento` (YYYY-MM-DD), `tipo`
- Response 201: dados do lançamento criado com `origem="proprio"`

### `GET /lancamentos`
- Autenticação: obrigatória
- Response 200: lista dos lançamentos do usuário, do mais recente ao mais antigo

### `GET /parceiro/pendentes/contagem`
- Autenticação: obrigatória
- Response 200: `{ total: N }` — quantidade de pendências do usuário autenticado
- Usado pelo frontend para o badge no menu (poll a cada 30s)

### `GET /parceiro/pendentes`
- Autenticação: obrigatória
- Response 200: lista de `lancamentos_parceiro` com `status="pendente"` para o usuário

### `POST /parceiro/{id}/aceitar`
- Autenticação: obrigatória
- Body: `versao_esperada` (integer)
- Response 200: mensagem de confirmação
- Comportamento: cria `lancamento` com `origem="compartilhado"` + atualiza registro para `aceito`
- Erros: 404 não encontrado, 400 já processado, 409 conflito de versão

### `POST /parceiro/{id}/ignorar`
- Autenticação: obrigatória
- Body: `versao_esperada` (integer)
- Response 200: mensagem de confirmação
- Erros: 404, 400 já processado, 409 conflito de versão

---

## Sincronizador (job em background)

**Biblioteca:** `apscheduler==3.10.4` — adicionar ao `requirements.txt`.

**Configuração:** `AsyncIOScheduler` iniciado via `lifespan` do FastAPI. O `lifespan` é um `asynccontextmanager` que inicia o scheduler antes do `yield` e faz `shutdown()` após.

**Intervalo:** 60 segundos.

**Lógica da função `executar_sincronizacao()`:**
1. Abre uma sessão de banco própria (fora do ciclo de requisição HTTP)
2. Busca todos os lançamentos `origem="proprio"` cujo `usuario_id` tem um registro em `conexoes_casal`
3. Para cada lançamento, verifica se já existe `lancamentos_parceiro` para o `usuario_parceiro_id` correspondente
4. Se não existe: cria com `status="pendente"` e snapshot dos dados atuais
5. É idempotente — pode rodar múltiplas vezes sem criar duplicatas

---

## Regras de negócio

- Um lançamento só é compartilhado **uma vez** (verificação `ja_existe_registro` antes de criar)
- A aceitação e a criação do lançamento do parceiro devem ocorrer na **mesma transação** de banco
- `versao_esperada` deve ser igual ao `versao_fonte` atual — protege contra dois cliques simultâneos
- Usuário só vê e processa seus próprios pendentes (`usuario_parceiro_id = usuario_autenticado`)

---

## Frontend

### Badge de pendentes
- `GET /parceiro/pendentes/contagem` chamado a cada 30 segundos após o login
- Número exibido no item "Parceiro" na sidebar
- Zera ao processar todos os itens

### Tela `/lancamentos-parceiro`
- Lista de cards com: descrição, valor (formatado como BRL), data, tipo (despesa/receita)
- Dois botões por item: "Aceitar" e "Ignorar"
- Após ação: item some da lista, badge decrementa
- Estado vazio: mensagem informando que nenhum lançamento aguarda ação
- Enquanto processa: botões desabilitados para aquele item

### Painel mínimo (tela `/painel`)
- Formulário simples para criar lançamento: descrição, valor, data, tipo (dropdown)
- Apenas para testar o fluxo do sincronizador (esta tela evolui na tarefa de lançamentos)
- Exibe mensagem de sucesso informando o prazo de até 60s para o parceiro ser notificado

### Iniciar polling
- `ParceiroService.iniciarPolling()` chamado após login bem-sucedido
- `ParceiroService.pararPolling()` chamado no logout

### Adicionar ao menu lateral
- Item "Parceiro" com ícone `heroUsers` apontando para `/lancamentos-parceiro`

---

## Verificação

```bash
# 1. Tabelas criadas
psql -U postgres casaleconomia_dev -c "\dt"
# esperado: lancamentos, lancamentos_parceiro

# 2. API inicia com mensagem do scheduler nos logs
# esperado: "[sincronizador] Agendador iniciado..."

# 3. Eduardo cria lançamento
curl -s -X POST http://localhost:8000/lancamentos \
  -H "Authorization: Bearer $TOKEN_EDUARDO" \
  -H "Content-Type: application/json" \
  -d '{"descricao":"Mercado","valor":"120.50","data_lancamento":"2026-11-09","tipo":"despesa"}'
# esperado: 201

# 4. Aguardar 60s — verificar pendentes como Tamires
curl -s http://localhost:8000/parceiro/pendentes -H "Authorization: Bearer $TOKEN_TAMIRES"
# esperado: 1 item com snapshot_descricao="Mercado"

# 5. Tamires aceita
curl -s -X POST http://localhost:8000/parceiro/<ID>/aceitar \
  -H "Authorization: Bearer $TOKEN_TAMIRES" \
  -H "Content-Type: application/json" \
  -d '{"versao_esperada":0}'
# esperado: mensagem de confirmação

# 6. Lançamento na carteira da Tamires
curl -s http://localhost:8000/lancamentos -H "Authorization: Bearer $TOKEN_TAMIRES"
# esperado: lançamento com origem="compartilhado"

# 7. Contagem zerada
curl -s http://localhost:8000/parceiro/pendentes/contagem -H "Authorization: Bearer $TOKEN_TAMIRES"
# esperado: {"total":0}
```

---

## Fora do escopo

- Notificar parceiro quando o dono EDITA ou EXCLUI um lançamento (próxima iteração)
- CRUD completo de lançamentos (tela com filtros, edição, exclusão)
- Categorias, contas, recorrência, parcelamento
