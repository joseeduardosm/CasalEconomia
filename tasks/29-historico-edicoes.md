# T29 — Histórico de edições de lançamentos

## Objetivo
Registrar toda alteração feita em um lançamento financeiro — quem editou, quando, quais campos
mudaram e os valores anterior e posterior. Para casais, isso cria transparência e rastreabilidade
sobre modificações em registros compartilhados.

---

## Contexto e motivação
Quando dois usuários compartilham lançamentos, qualquer um pode editar. Sem histórico, se um valor
ou descrição mudar, o outro parceiro não sabe quem alterou e o que estava antes. O histórico de
edições resolve isso com transparência sem burocracia.

---

## Dados do histórico

### Nova tabela: `lancamento_historico`

| Coluna          | Tipo       | Descrição                                                   |
| --------------- | ---------- | ----------------------------------------------------------- |
| `id`            | UUID PK    | Identificador da entrada                                    |
| `lancamento_id` | FK         | Lançamento auditado                                         |
| `usuario_id`    | FK         | Quem realizou a ação                                        |
| `usuario_nome`  | texto      | Nome do usuário no momento (retrato)                        |
| `acao`          | texto      | `criado`, `editado`, `pago`, `nao_pago`, `excluido`         |
| `campos`        | JSON       | Array de `{campo, antes, depois}` (só nos `editado`)        |
| `criado_em`     | timestamptz| Data e hora da ação                                         |

### Campos rastreados em `editado`

| Campo interno       | Rótulo exibido         |
| ------------------- | ---------------------- |
| `descricao`         | Descrição              |
| `valor`             | Valor                  |
| `data`              | Data                   |
| `forma_pagamento`   | Forma de pagamento     |
| `categoria_id`      | Categoria              |
| `conta_id`          | Conta                  |
| `cartao_id`         | Cartão                 |
| `nota`              | Nota                   |
| `pago`              | Status de pagamento    |

---

## Regras de registro

1. Toda criação de lançamento gera uma entrada `acao = "criado"` sem `campos`.
2. Toda edição gera `acao = "editado"` com apenas os campos que mudaram de fato.
3. Marcar como pago/não pago via endpoint dedicado gera `acao = "pago"` / `acao = "nao_pago"`.
4. Exclusão gera `acao = "excluido"`.
5. `usuario_nome` é copiado no momento do registro (retrato imutável).
6. O histórico pertence ao dono do lançamento (`usuario_id` do lançamento), não ao editor —
   ambos os parceiros de um lançamento compartilhado podem ver o histórico.
7. O histórico nunca é editado nem deletado manualmente — é append-only.

---

## Endpoints

### `GET /lancamentos/{id}/historico`
Retorna a lista de eventos em ordem cronológica decrescente.

**Resposta:**
```json
{
  "data": [
    {
      "id": "...",
      "acao": "editado",
      "usuario_nome": "Maria",
      "criado_em": "2026-11-08T18:42:00Z",
      "campos": [
        { "campo": "valor", "antes": "150.00", "depois": "200.00" },
        { "campo": "descricao", "antes": "Supermercado", "depois": "Supermercado BH" }
      ]
    }
  ]
}
```

---

## UI — Painel lateral de histórico

### Abertura
- Botão **"Histórico"** (ícone relógio) no `DrawerDetalheComponent` (drawer de detalhe do
  lançamento).

### Layout do painel
- Linha do tempo vertical, entrada mais recente no topo.
- Cada linha: avatar/iniciais do autor + nome + data relativa + ação em texto natural.
  - `criado` → _"João criou este lançamento"_
  - `editado` → _"Maria editou: Valor de R$ 150,00 para R$ 200,00; Descrição alterada"_
  - `pago` → _"João marcou como pago"_
  - `nao_pago` → _"Maria marcou como não pago"_
  - `excluido` → _(registro excluído; visto apenas por quem tem permissão — fora do escopo MVP)_
- Sem paginação no MVP (máx. 50 entradas exibidas).

---

## Integração com lançamentos compartilhados
- Quando o lançamento é compartilhado com o parceiro, ambos podem ver o histórico.
- Se o editor for o parceiro, o nome exibido é o nome do parceiro.

---

## Verificação

```
# Criar lançamento e verificar entrada "criado"
curl -s -X GET http://localhost:8000/api/lancamentos/<id>/historico \
  -H "Cookie: session=..." | jq '.data[0].acao'
# → "criado"

# Editar descrição e valor, verificar campos alterados
curl -s -X PATCH http://localhost:8000/api/lancamentos/<id> \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"descricao": "Novo nome", "valor": 300}' && \
curl -s -X GET http://localhost:8000/api/lancamentos/<id>/historico \
  -H "Cookie: session=..." | jq '.data[0]'
# → acao "editado", campos com antes/depois de descricao e valor

# Marcar como pago
curl -s -X PATCH http://localhost:8000/api/lancamentos/<id>/pago \
  -H "Cookie: session=..." && \
curl -s -X GET http://localhost:8000/api/lancamentos/<id>/historico \
  -H "Cookie: session=..." | jq '.data[0].acao'
# → "pago"
```

---

## Fora de escopo

- Histórico de transferências (entidade separada, escopo futuro).
- Histórico de contas, cartões, metas (escopo futuro).
- Reverter edição a partir do histórico.
- Exportação do histórico em PDF/XLSX.
- Retenção configurável (todos os registros são guardados indefinidamente no MVP).
