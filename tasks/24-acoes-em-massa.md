# Tarefa 24 — Ações em Massa nas Tabelas

## Contexto

Adiciona seleção múltipla e ações em lote ao `TabelaLancamentosComponent` (tarefa 11).
O usuário pode selecionar vários lançamentos de uma vez e executar uma ação sobre todos
simultaneamente: marcar como pago, marcar como não pago, alterar categoria, alterar descrição
ou excluir.

Elimina o trabalho repetitivo de abrir cada lançamento individualmente quando a operação é
a mesma para vários registros — exemplo: marcar todas as faturas do mês como pagas, recategorizar
importações do OFX, excluir lançamentos duplicados.

**Nenhuma nova tabela.** Apenas endpoints de bulk no backend e UI de seleção no frontend.

**Pré-requisito:** tarefas 01–23 concluídas. Requer tarefas 11 (tabela), 15 (contas), 17 (categorias).

---

## Regras de negócio

### Autorização de ownership

Todo endpoint de ações em massa valida que **cada** ID da lista pertence ao usuário autenticado
antes de executar qualquer ação. Se qualquer ID não pertencer ao usuário: 403 imediato,
sem executar nada.

### Atomicidade parcial vs total

- Ações de edição (marcar pago, categoria, descrição): execução em lote dentro de uma única
  transação de banco — tudo ou nada. Se qualquer item falhar validação de negócio, retornar
  erro com detalhe; nenhum item é alterado.
- Exclusão em massa: mesma regra — exclusão atômica de todos os IDs ou nenhum.
- Exceção: se o frontend enviar IDs de lançamentos de tipos incompatíveis (ex: marcar como
  pago um lançamento sem `data_vencimento`), o backend rejeita apenas os IDs inválidos e
  processa os válidos — retornando `processados` e `ignorados` com motivo.

### Marcar como pago / não pago

- Marcar como pago: `liquidado = true`, `data_liquidacao = hoje` (se ainda não preenchida)
- Marcar como não pago: `liquidado = false`, `data_liquidacao = null`
- Sem restrição de tipo (receitas e despesas)

### Alterar categoria em massa

- Recebe `categoria_id` (UUID da nova categoria)
- Valida que a categoria pertence ao usuário ou é padrão do sistema
- Aplica para todos os IDs selecionados

### Alterar descrição em massa

- Recebe `descricao` (string)
- Útil para padronizar nomes após importação OFX (ex: "COMPRA IFOOD" → "iFood")
- Aplica para todos os IDs selecionados

### Excluir em massa

- Lançamentos vinculados a parcelamento (`serie_id`): a exclusão em massa remove somente os
  lançamentos selecionados individualmente, sem excluir a série. Se o usuário quiser excluir
  a série inteira, deve fazê-lo pelo detalhe do parcelamento.
- Lançamentos de transferência (`transferencia_id`): a exclusão de um lado cancela a
  transferência inteira; o backend informa que o lançamento espelho também foi excluído.
- Sem soft-delete — exclusão em massa é definitiva; modal de confirmação obrigatório no frontend.

---

## Endpoints

### `PATCH /lancamentos/em-massa/pago`
- Autenticação: obrigatória
- Body: `ids: [UUID]`, `liquidado: bool`
- Validação: ownership de todos os IDs
- Response 200: `{ "processados": int, "ignorados": [{ "id": UUID, "motivo": str }] }`

### `PATCH /lancamentos/em-massa/categoria`
- Autenticação: obrigatória
- Body: `ids: [UUID]`, `categoria_id: UUID`
- Validação: ownership dos IDs; `categoria_id` acessível ao usuário
- Response 200: `{ "processados": int }`

### `PATCH /lancamentos/em-massa/descricao`
- Autenticação: obrigatória
- Body: `ids: [UUID]`, `descricao: str`
- Validação: ownership dos IDs; `descricao` não vazia
- Response 200: `{ "processados": int }`

### `DELETE /lancamentos/em-massa`
- Autenticação: obrigatória
- Body: `ids: [UUID]`
- Validação: ownership de todos os IDs; nenhum pode ter `lancamentos_parceiro.status = "aceito"`
  (lançamento compartilhado aceito não pode ser excluído em massa — deve ser gerenciado
  individualmente para notificar o parceiro)
- Response 200: `{ "excluidos": int, "efeitos": [{ "descricao": str }] }` — efeitos lista
  transferências canceladas etc.

---

## Atualizar `TabelaLancamentosComponent` (tarefa 11)

### Novo input

| Input | Tipo | Descrição |
|---|---|---|
| `permitirSelecao` | `boolean` | default `false` — ativa o modo de seleção múltipla |
| `acoesPermitidas` | `AcaoMassaConfig[]` | lista de ações habilitadas para esta tabela |

### `AcaoMassaConfig`

```
{
  tipo: 'marcar_pago' | 'marcar_nao_pago' | 'alterar_categoria' |
        'alterar_descricao' | 'excluir',
  rotulo: string
}
```

### Comportamento de seleção

- Quando `permitirSelecao = true`: primeira coluna da tabela é um checkbox por linha
- Cabeçalho: checkbox "Selecionar todos" (marca/desmarca todos os itens visíveis após filtro)
- Contador de selecionados: "X selecionados" na barra de ações (aparece ao selecionar ≥ 1)
- Tecla `Escape`: deseleciona todos
- Seleção persiste ao ordenar ou filtrar (IDs mantidos independente da paginação visual)

### Barra de ações em massa

Aparece acima da tabela (substituindo ou ao lado da barra de busca) quando ≥ 1 item selecionado:

```
[ X selecionados ]  [ Marcar como pago ▾ ]  [ Alterar categoria ]
                    [ Alterar descrição ]  [ Excluir ]  [ Cancelar seleção ]
```

- Dropdown "Marcar como..." com opções "Pago" e "Não pago"
- Cada ação abre `ModalAcaoMassaComponent` para confirmação e entrada de dados

### `ModalAcaoMassaComponent`

Modal genérico para ações em massa:

**Marcar pago / não pago:**
- Texto: "Marcar X lançamentos como pagos?"
- Botões: Cancelar | Confirmar

**Alterar categoria:**
- Select de categoria (igual ao modal de lançamento — tarefa 17)
- Texto: "Alterar categoria de X lançamentos para [selecionado]?"
- Botões: Cancelar | Confirmar

**Alterar descrição:**
- Input de texto obrigatório
- Aviso: "Esta ação sobrescreve a descrição atual de X lançamentos"
- Botões: Cancelar | Confirmar

**Excluir:**
- Texto: "Esta ação excluirá permanentemente X lançamentos. Não pode ser desfeita."
- Input de confirmação: "Digite EXCLUIR para confirmar" (apenas para seleções > 5 itens)
- Botão vermelho: "Excluir X lançamentos"

### Onde habilitar

| Componente | `permitirSelecao` | Ações habilitadas |
|---|---|---|
| `LancamentosComponent` (`/lancamentos`) | `true` | todas |
| `DrawerDetalheComponent` (painel — T09) | `false` | — |
| `FaturaDetalheComponent` (`/cartoes/:id/fatura`) | `true` | marcar_pago, excluir |
| `ExtratoContaComponent` (`/contas/:id/extrato`) | `true` | marcar_pago, alterar_categoria, excluir |
| `VisaoCompartilhadaComponent` (casal — T13) | `false` | — (lançamentos do parceiro não são editáveis) |

### `AcoesMassaService` (Angular, singleton)

Métodos: `marcarPago(ids, liquidado)`, `alterarCategoria(ids, categoriaId)`,
`alterarDescricao(ids, descricao)`, `excluir(ids)`

---

## Verificação

```bash
# 1. Marcar vários lançamentos como pagos
curl -s -X PATCH http://localhost:8000/lancamentos/em-massa/pago \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ids":["<uuid1>","<uuid2>","<uuid3>"],"liquidado":true}' \
  | python3 -m json.tool
# esperado: processados=3

# 2. Alterar categoria em massa
curl -s -X PATCH http://localhost:8000/lancamentos/em-massa/categoria \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ids":["<uuid1>","<uuid2>"],"categoria_id":"<uuid-categoria>"}' \
  | python3 -m json.tool
# esperado: processados=2

# 3. Excluir em massa
curl -s -X DELETE http://localhost:8000/lancamentos/em-massa \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"ids":["<uuid4>","<uuid5>"]}' | python3 -m json.tool
# esperado: excluidos=2

# 4. ID de outro usuário no lote → 403 (nenhum item processado)

# 5. Lançamento compartilhado aceito na lista de exclusão → 400 com motivo
```

Frontend:
- Abrir `/lancamentos` → primeira coluna com checkboxes
- Marcar 3 lançamentos → barra de ações aparece com "3 selecionados"
- Clicar "Marcar como pago" → modal de confirmação → confirmar → chips de status atualizam
- Clicar "Excluir" → modal com aviso → confirmar → lançamentos somem da tabela
- "Selecionar todos" marca todos os visíveis após filtro de busca
- Escape desmarca todos e oculta barra de ações

---

## Fora do escopo

- Ações em massa em recorrências (tarefa 16)
- Ação em massa de compartilhamento (definir % para múltiplos lançamentos)
- Desfazer ação em massa (undo — requer log de operações)
- Exportar selecionados como CSV/XLSX
- Ações em massa para metas ou contas
