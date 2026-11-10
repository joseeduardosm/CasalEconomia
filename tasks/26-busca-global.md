# Tarefa 26 — Busca Global

## Contexto

Implementa uma barra de busca global acessível em qualquer tela da aplicação — atalho de
teclado ou ícone na barra de topo — que pesquisa simultaneamente em lançamentos, contas,
cartões, metas, recorrências e categorias, retornando resultados agrupados por tipo com
navegação direta ao item.

A busca da tarefa 11 é **por tabela** (client-side, dados já carregados em memória). A busca
global é **cross-entidade** (server-side, qualquer mês, qualquer entidade) e retorna links de
navegação para o item encontrado.

**Pré-requisito:** tarefas 01–25 concluídas.

---

## Escopo da busca

| Entidade | Campos pesquisados | Destino ao clicar |
|---|---|---|
| `lancamentos` | `descricao`, `categoria.nome`, `nota`, `nome_devedor` | `/lancamentos?id=<id>` (abre detalhe) |
| `contas` | `nome` | `/contas/<id>/extrato` |
| `cartoes` | `nome`, `bandeira` | `/cartoes/<id>` |
| `metas` | `nome`, `categoria.nome` | `/metas/<id>` |
| `orcamentos` | `categoria.nome` | `/orcamento` (scroll até o card) |
| `recorrencias` | `descricao`, `categoria` | `/recorrencias/<id>` |
| `categorias` | `nome` | `/configuracoes/categorias` |

---

## Regras de negócio

### Escopo de ownership

Todos os resultados filtrados por `usuario_id` autenticado. Lançamentos do parceiro **não**
aparecem na busca global (cada usuário vê apenas seus próprios dados).

### Busca por texto

- Case-insensitive
- Sem acento (normalização `unaccent` via extensão PostgreSQL — `CREATE EXTENSION unaccent`)
- Match parcial: `ILIKE '%termo%'` nos campos mapeados
- Termo mínimo: 2 caracteres (abaixo disso: retornar lista vazia sem consulta)

### Limite de resultados

- Máximo 5 resultados por entidade
- Máximo 25 resultados no total
- Lançamentos: preferência por mais recentes (ORDER BY `data_lancamento DESC`)
- Demais entidades: por relevância (match exato no início do campo primeiro)

### Busca de lançamentos

- Pesquisa em **todos os meses** (sem filtro de período) — diferente da busca da tabela que
  opera apenas nos dados carregados do mês atual
- Exibe data do lançamento no resultado para localizar temporalmente

---

## Endpoint

### `GET /busca`
- Autenticação: obrigatória
- Query param: `q` (string, min 2 chars)
- Response 200:
  ```
  {
    "query": str,
    "total": int,
    "grupos": [
      {
        "entidade": "lancamentos" | "contas" | "cartoes" | "metas" |
                    "orcamentos" | "recorrencias" | "categorias",
        "rotulo": str,         // "Lançamentos", "Contas", etc.
        "icone": str,          // nome do heroicon para o grupo
        "resultados": [
          {
            "id": UUID,
            "titulo": str,       // campo principal (ex: lancamento.descricao)
            "subtitulo": str,    // campo secundário (ex: "R$ 45,00 · 09/11/2026")
            "link": str,         // rota de navegação
            "icone": str | null  // ícone da categoria ou forma de pagamento (opt)
          }
        ]
      }
    ]
  }
  ```
- Retornar apenas grupos com ao menos 1 resultado
- Se `q` tiver menos de 2 caracteres: 200 com `grupos: []`

---

## Frontend

### Barra de busca global (`BuscaGlobalComponent`)

Localização: ícone `heroMagnifyingGlass` na barra de topo (`BarraTopoComponent`), ao lado do
seletor de mês. Também acessível pelo atalho de teclado **Ctrl+K** (ou Cmd+K no Mac).

### Comportamento do modal de busca

- Atalho Ctrl+K ou clique no ícone → abre modal/command-palette centralizado
- Input de texto com foco automático ao abrir
- Placeholder: "Buscar em qualquer lugar..."
- Debounce de 400ms antes de chamar `GET /busca`
- Spinner discreto enquanto carrega
- Resultados agrupados por entidade com cabeçalho de grupo (ícone + rótulo)
- Navegação com teclado: `↑` `↓` para mover entre resultados, `Enter` para abrir,
  `Escape` para fechar
- Clique em resultado → navega para `link` e fecha o modal
- Estado vazio: "Nenhum resultado para '[termo]'"
- Estado inicial (antes de digitar): mostrar atalhos úteis ou recentes (últimas 5 buscas
  armazenadas em `localStorage`)

### Layout do modal

```
┌────────────────────────────────────────┐
│  🔍 |  Buscar em qualquer lugar...     │
├────────────────────────────────────────┤
│  LANÇAMENTOS                           │
│  > iFood · R$ 45,00 · 09/11/2026      │
│  > iFood · R$ 32,00 · 02/11/2026      │
├────────────────────────────────────────┤
│  CATEGORIAS                            │
│  > Alimentação                         │
│  > Fast food (personalizada)           │
├────────────────────────────────────────┤
│  Pressione ↑↓ para navegar · Enter para abrir · Esc para fechar │
└────────────────────────────────────────┘
```

### `BuscaGlobalService` (Angular, singleton)

Métodos: `buscar(query)`, `salvarRecente(resultado)`, `listarRecentes()`

---

## Verificação

```bash
# 1. Busca por descrição de lançamento
curl -s "http://localhost:8000/busca?q=ifood" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: grupo "lancamentos" com lançamentos cujo descricao ILIKE '%ifood%'

# 2. Busca por nome de conta
curl -s "http://localhost:8000/busca?q=nubank" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: grupo "contas" com contas cujo nome ILIKE '%nubank%'

# 3. Busca com acento vs sem acento
# lançamento com descricao="Supermercado São Paulo"
curl -s "http://localhost:8000/busca?q=sao+paulo" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: encontra mesmo sem acento

# 4. Busca com menos de 2 caracteres → 200 com grupos=[]
curl -s "http://localhost:8000/busca?q=a" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 5. Busca que não encontra nada → 200 com total=0, grupos=[]

# 6. Lançamento do parceiro → não aparece nos resultados
```

Frontend:
- Pressionar Ctrl+K → modal abre com foco no input
- Digitar "ifood" → resultados aparecem agrupados em "Lançamentos"
- Digitar "nubank" → resultado em "Contas"
- Usar ↓ para navegar → item destacado
- Pressionar Enter → navega para o lançamento; modal fecha
- Pressionar Escape → modal fecha sem navegar
- Reabrir modal → últimas buscas sugeridas

---

## Fora do escopo

- Busca full-text com ranking por relevância (PostgreSQL `tsvector`) — ILIKE é suficiente para MVP
- Busca por valor exato (ex: "R$ 45,00")
- Busca por intervalo de datas
- Indexação de conteúdo de anexos (OCR)
- Busca nos dados do parceiro
- Sugestões de autocompletar baseadas em histórico do usuário
- Busca federada em múltiplos workspaces
