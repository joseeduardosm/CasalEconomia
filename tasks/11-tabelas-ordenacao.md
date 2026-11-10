# Tarefa 11 — Tabelas Ordenáveis e Busca em Tempo Real

## Contexto

Aplica dois comportamentos de UX em **todas as visões de tabela de lançamentos** do projeto:
colunas ordenáveis por clique no cabeçalho e barra de busca de largura total que filtra a tabela
à medida que o usuário digita (client-side, sem nova chamada à API).

Implementado como um componente compartilhado `TabelaLancamentosComponent` para evitar duplicar
a lógica em cada tela.

**Nenhuma mudança de backend.** Nenhuma tabela nova.

**Pré-requisito:** tarefas 01–10 concluídas.

---

## Componente central: `TabelaLancamentosComponent`

Arquivo: `web/src/app/shared/components/tabela-lancamentos/tabela-lancamentos.component.ts`

### Inputs

| Input | Tipo | Descrição |
|---|---|---|
| `lancamentos` | `Lancamento[]` | Array já carregado pelo componente pai |
| `colunas` | `ColunaTabelaConfig[]` | Quais colunas exibir e em que ordem (ver abaixo) |
| `titulo` | `string` | Exibido acima da barra de busca (opcional) |
| `mostrarBusca` | `boolean` | default `true` |
| `mostrarTotal` | `boolean` | default `true` — rodapé com soma dos valores visíveis |

### `ColunaTabelaConfig`

```
{
  campo: 'descricao' | 'data_lancamento' | 'valor' | 'forma_pagamento' |
         'status' | 'categoria' | 'parcela' | 'fonte' | 'cartao_nome',
  rotulo: string,          // ex: "Descrição", "Data", "Valor"
  ordenavel: boolean,      // default true
  largura?: string         // ex: "180px" (opcional; sem valor = flex-grow)
}
```

### Ordenação

- Clique no cabeçalho de coluna ordenável → ordena ASC
- Segundo clique → DESC
- Terceiro clique → remove ordenação (volta à ordem original)
- Indicador visual: seta ↑ (ASC) / ↓ (DESC) no cabeçalho ativo; cor `--color-primary`
- Tipos de ordenação:
  - `descricao`, `categoria`, `fonte`, `forma_pagamento`, `cartao_nome`, `status` → string locale (`localeCompare`)
  - `data_lancamento` → date
  - `valor` → numeric
  - `parcela` → numeric (nullable — nulls vão para o fim)
- Ordenação padrão: `data_lancamento DESC`

### Busca em tempo real

- `<input>` de largura 100% acima da tabela
- Placeholder: "Buscar em [título]..." ou "Buscar lançamentos..."
- Debounce de 300ms
- Pesquisa simultânea em: `descricao`, `categoria`, `fonte`, `forma_pagamento`, `cartao_nome`
  e `valor` (formatado como string, ex: `"45,00"`)
- Busca case-insensitive e sem acento (normalizar com `.normalize('NFD').replace(/[̀-ͯ]/g, '')`)
- Contador abaixo da barra: "X de Y lançamentos" — atualizado em tempo real
- Estado vazio: "Nenhum lançamento encontrado para '[termo]'"
- Limpar busca: ícone `heroXMark` dentro do input (visível quando há texto)

### Rodapé

- Se `mostrarTotal = true`: linha de rodapé com "Total: R$ X" somando `valor` dos itens visíveis
  (após filtro de busca + ordenação)
- Receitas somadas em verde, despesas em vermelho, misto em neutro

---

## Onde aplicar

### 1. `LancamentosComponent` (`/lancamentos`)

Colunas: Descrição, Data, Valor, Forma de pagamento, Status, Categoria, Parcela

Comportamento atual de agrupamento por data é **substituído** pela tabela com ordenação.
O filtro de tipo (Todos / Despesas / Receitas) permanece acima da `TabelaLancamentosComponent`,
e o resultado filtrado é passado como input `lancamentos`.

### 2. `DrawerDetalheComponent` (painel — tarefa 09)

Colunas variam por contexto (configuradas pelo componente pai):
- Drawer de fatura: Descrição, Data, Valor, Parcela
- Drawer de tipo (receitas/despesas): Descrição, Data, Valor, Forma de pagamento, Status, Categoria

### 3. `FaturaDetalheComponent` (`/cartoes/:id/fatura`)

Colunas: Descrição, Data, Valor, Parcela
Substituir a lista atual por `TabelaLancamentosComponent`.

### 4. `ExtratoContaComponent` (`/contas/:id/extrato` — tarefa 15)

Colunas: Descrição, Data, Valor, Forma de pagamento, Status
Usará `TabelaLancamentosComponent` desde a criação.

---

## Responsividade

**Desktop (≥ 768px):** todas as colunas configuradas são exibidas.

**Mobile (< 768px):** exibir no máximo 3 colunas. Colunas de baixa prioridade são ocultadas
automaticamente nesta ordem de exclusão: Forma de pagamento → Categoria → Parcela → Fonte.
Sempre exibir: Descrição, Valor, Data.

Linha da tabela clicável no mobile abre um popover com os campos ocultos.

---

## Novos arquivos

```
web/src/app/shared/components/
  tabela-lancamentos/
    tabela-lancamentos.component.ts
    tabela-lancamentos.component.html
    tabela-lancamentos.component.scss
```

## Componentes existentes a atualizar

| Componente | Mudança |
|---|---|
| `LancamentosComponent` | Substituir lista manual por `TabelaLancamentosComponent` |
| `DrawerDetalheComponent` | Substituir tabela manual por `TabelaLancamentosComponent` |
| `FaturaDetalheComponent` | Substituir lista de lançamentos por `TabelaLancamentosComponent` |

`ExtratoContaComponent` (tarefa 15) já nasce usando o componente.

---

## Verificação

Frontend:
- Abrir `/lancamentos` → ver barra de busca e cabeçalhos com seta de ordenação
- Clicar no cabeçalho "Valor" → ordena do menor para o maior (ASC)
- Clicar novamente → ordena do maior para o menor (DESC)
- Clicar uma terceira vez → remove ordenação, volta à ordem original (data DESC)
- Digitar "Uber" na barra de busca → tabela filtra instantaneamente; contador mostra "X de Y"
- Digitar com acento ("ônibus") → encontra lançamentos com "onibus" (sem acento) e vice-versa
- Limpar a busca (×) → todos os lançamentos voltam
- Abrir painel → clicar em card "Despesas" → drawer abre com `TabelaLancamentosComponent`
  já com busca e ordenação funcionando
- Abrir fatura de cartão → lista de lançamentos tem cabeçalhos ordenáveis e barra de busca
- Reduzir janela para mobile → colunas secundárias somem; clicar em linha exibe popover com detalhes

---

## Fora do escopo

- Paginação (os dados de um mês cabem na tela sem paginar)
- Filtros avançados por intervalo de datas ou faixa de valor (tarefa de relatórios)
- Exportação CSV/XLSX da tabela
- Busca server-side (todos os dados do mês já estão em memória)
- Seleção múltipla de linhas para ação em lote
