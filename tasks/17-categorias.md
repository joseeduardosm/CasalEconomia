# Tarefa 17 — Categorias com Ícones e Cores

## Contexto

Hoje o campo `categoria` em `lancamentos`, `metas` e relatórios é texto livre (`VARCHAR(80)`).
Isso causa inconsistências: "Restaurante", "restaurante", "Restaurantes" tratados como três
categorias distintas no relatório de distribuição (tarefa 12) e metas de limite de gasto
(tarefa 14) que não batem com lançamentos digitados de forma diferente.

Esta tarefa cria uma tabela `categorias` com nome canônico, ícone heroicons e cor para exibição
visual consistente, além de ~20 categorias-padrão criadas automaticamente no primeiro uso.

**Pré-requisito:** tarefas 01–16 concluídas.

---

## Nova tabela

### `categorias`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | dono (ou `null` para categorias globais padrão) |
| `nome` | VARCHAR(80) | sim | único por usuario_id; case-insensitive ao salvar |
| `icone_nome` | VARCHAR(60) | sim | nome do heroicon (ex: `heroShoppingCart`) |
| `cor` | VARCHAR(7) | sim | hex (#RRGGBB) |
| `tipo_padrao` | VARCHAR(10) | não | `receita` / `despesa` / `ambos` — dica de filtro na UI |
| `padrao` | BOOLEAN | sim | `true` se é categoria pré-instalada do sistema |
| `arquivada_em` | TIMESTAMPTZ | não | soft-delete |
| `criado_em` | TIMESTAMPTZ | sim | |

### Alteração em `lancamentos`

Adicionar coluna `categoria_id UUID FK → categorias.id` (nullable).
O campo texto `categoria` VARCHAR(80) é **mantido** por compatibilidade durante a migração.
Após migração de dados, `categoria` passa a ser derivado de `categorias.nome`.

---

## Categorias padrão do sistema

Criadas via migration com `usuario_id = null` e `padrao = true`. Disponíveis para todos os
usuários. Não podem ser editadas nem arquivadas pelo usuário (somente pelo admin do sistema).

| Nome | Ícone | Cor | Tipo padrão |
|---|---|---|---|
| Alimentação | heroShoppingCart | #22c55e | despesa |
| Restaurante | heroFire | #f97316 | despesa |
| Transporte | heroCar | #3b82f6 | despesa |
| Moradia | heroHome | #8b5cf6 | despesa |
| Saúde | heroHeart | #ef4444 | despesa |
| Educação | heroAcademicCap | #06b6d4 | despesa |
| Lazer | heroMusicalNote | #ec4899 | despesa |
| Vestuário | heroTag | #f59e0b | despesa |
| Tecnologia | heroComputerDesktop | #6366f1 | despesa |
| Viagem | heroPaperAirplane | #0ea5e9 | despesa |
| Pets | heroHeart | #84cc16 | despesa |
| Academia | heroBolt | #f97316 | despesa |
| Beleza | heroSparkles | #d946ef | despesa |
| Farmácia | heroPlusCircle | #ef4444 | despesa |
| Serviços | heroWrenchScrewdriver | #78716c | despesa |
| Impostos | heroDocumentText | #94a3b8 | despesa |
| Investimento | heroArrowTrendingUp | #22c55e | ambos |
| Salário | heroBriefcase | #22c55e | receita |
| Freelance | heroComputerDesktop | #3ba6f1 | receita |
| Outro | heroEllipsisHorizontal | #78716c | ambos |

---

## Regras de negócio

### Criação de categoria personalizada

- Usuário pode criar categorias próprias além das padrão
- Nome único por usuário (case-insensitive): "Pets" e "pets" são a mesma categoria
- Escolhe entre ícones heroicons disponíveis (lista fornecida pela UI) e cor hex
- Categoria personalizada pode ser arquivada (soft-delete); lançamentos vinculados mantêm o vínculo

### Vínculo com lançamentos

- Ao criar/editar um lançamento, o campo `categoria` é substituído por um select de `categorias`
- O select mostra ícone + nome de cada categoria; filtrado por `tipo_padrao` conforme o tipo de lançamento
- Ao salvar: `categoria_id` é preenchido; `categoria` (texto) recebe `categorias.nome` para retrocompatibilidade
- Lançamentos antigos sem `categoria_id` mantêm o texto livre; a UI exibe o texto sem ícone

### Migração de dados existentes

Script de migração (Alembic) tenta casar texto livre de `lancamentos.categoria` com
`categorias.nome` (case-insensitive). Casamentos exatos preenchem `categoria_id`. Textos sem
correspondência permanecem com `categoria_id = null` e texto original preservado.

### Categorias nas metas (`limite_gasto`)

A meta de `limite_gasto` passa a referenciar `categoria_id` em vez de texto livre. O campo texto
`categoria` em `metas` é mantido para retrocompatibilidade durante a migração.

---

## Endpoints

### `GET /categorias`
- Autenticação: obrigatória
- Retorna categorias padrão do sistema + categorias personalizadas do usuário autenticado
- Query param: `tipo` (receita/despesa/ambos — filtra por `tipo_padrao`)
- Exclui arquivadas por padrão; `incluir_arquivadas=true` para incluir
- Response 200: lista ordenada (padrão primeiro, depois personalizadas por nome)

### `POST /categorias`
- Autenticação: obrigatória
- Body: `nome`, `icone_nome`, `cor`, `tipo_padrao`
- Response 201: categoria criada

### `PUT /categorias/{id}`
- Autenticação: obrigatória — somente categorias personalizadas do próprio usuário
- Body: `nome`, `icone_nome`, `cor`, `tipo_padrao`
- Response 200: categoria atualizada

### `DELETE /categorias/{id}`
- Autenticação: obrigatória — somente categorias personalizadas do próprio usuário
- Categorias padrão do sistema: 403
- Categorias com lançamentos vinculados: soft-delete (arquivada_em)
- Sem lançamentos vinculados: exclusão física
- Response 200

---

## Frontend

### Select de categoria nos modais (tarefas 07/08)

Substituir `<input type="text">` de categoria por `<select>` com `CategoriaSelectorComponent`:
- Cada opção exibe `icone_pagamento` + nome (reutiliza `IconePagamentoComponent` adaptado)
- Opção "Criar nova categoria" no final da lista → abre `ModalCriarCategoriaComponent`
- Filtra automaticamente categorias pelo `tipo_padrao` compatível com o lançamento atual

### `ModalCriarCategoriaComponent`

- Campo nome (obrigatório, único)
- Seletor de ícone: grid 5×6 de ícones heroicons disponíveis
- Seletor de cor: paleta de 16 cores predefinidas + campo hex personalizado
- Radio `tipo_padrao`: Despesa / Receita / Ambos
- Botões: Cancelar | Salvar

### Tela `/configuracoes/categorias` (sub-rota de configurações — tarefa 19)

- Lista de categorias personalizadas com ícone, nome, cor, tipo
- Botão "+ Nova categoria"
- Ações por item: Editar, Arquivar
- Categorias padrão do sistema exibidas em seção separada (somente leitura)

### Exibição em relatórios e metas

- Relatório R1 (distribuição): cada linha de categoria mostra ícone + cor
- Relatório R2 (tendência): cada série do gráfico usa a cor da categoria
- Widget de metas (painel): `limite_gasto` mostra ícone da categoria monitorada

### `CategoriasService` (Angular, singleton)

Métodos: `listar(filtros)`, `criar(dados)`, `atualizar(id, dados)`, `arquivar(id)`

---

## Verificação

```bash
# 1. Listar categorias disponíveis
curl -s http://localhost:8000/categorias \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: ~20 categorias padrão + personalizadas do usuário

# 2. Criar categoria personalizada
curl -s -X POST http://localhost:8000/categorias \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"Delivery","icone_nome":"heroTruck","cor":"#f97316","tipo_padrao":"despesa"}' \
  | python3 -m json.tool
# esperado: 201 com id

# 3. Tentar criar categoria com nome duplicado → 409 ou 422

# 4. Tentar editar categoria padrão do sistema → 403

# 5. Criar lançamento com categoria_id preenchido
# GET /lancamentos → lançamento retorna categoria com icone_nome e cor

# 6. Relatório de distribuição após criar lançamentos com categorias
curl -s "http://localhost:8000/relatorios/distribuicao?mes_inicio=2026-11&mes_fim=2026-11" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: por_categoria com icone_nome e cor em cada item

# 7. Meta de limite_gasto com categoria_id
# esperado: gasto calculado casa com lançamentos da mesma categoria_id
```

Frontend:
- Abrir modal de despesa → campo categoria é select com ícones
- Selecionar "Alimentação" → ícone exibido ao lado do nome
- Clicar "Criar nova categoria" → modal abre; preencher; nova categoria aparece no select
- Relatório R1 → barras de categoria com cor e ícone
- Relatório R2 → linhas do gráfico com cores das categorias

---

## Fora do escopo

- Categorias hierárquicas (pai / filho)
- Categorias compartilhadas com o parceiro
- Sugestão automática de categoria por descrição do lançamento (ML)
- Orçamento por categoria separado de metas (tarefa 19 pode cobrir isso)
- Importação/exportação de categorias personalizadas
