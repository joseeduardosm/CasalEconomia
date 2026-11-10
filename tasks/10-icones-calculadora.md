# Tarefa 10 — Ícones na Navbar, Modais de Lançamento e Modal de Calculadora

## Contexto

Polimento de UX em três frentes sem nenhuma mudança de backend:

1. **Navbar com badge de pendentes e avatar** — a sidebar ganha badge numérico no item
   "Lançamentos" quando o parceiro tem itens aguardando aceite, e um avatar com iniciais do
   usuário no rodapé.

2. **Ícones de forma de pagamento** — os selects de `forma_pagamento` nos modais de despesa e
   receita exibem ícones coloridos ao lado de cada opção; a lista de lançamentos e o widget de
   recentes do painel também mostram esses ícones.

3. **Modal de calculadora** — botão ao lado do campo `valor` em ambos os modais de lançamento.
   Abre um teclado numérico de 4 operações; o resultado preenche o campo ao confirmar.

**Pré-requisito:** tarefas 01–09 concluídas.

---

## 1. Badge de pendentes na navbar

### Polling de contagem
O `NavLateralComponent` e o `NavMobileComponent` consultam `GET /parceiro/pendentes/contagem`
(endpoint já existente da tarefa 05) a cada 30 segundos usando `setInterval` no `ngOnInit`,
cancelado no `ngOnDestroy`. O resultado `{ "contagem": N }` é armazenado num signal local
`pendentesCount`.

O polling só é iniciado quando o usuário tem parceiro conectado. O `AuthService` deve expor
`temParceiro(): boolean` — verificado na primeira carga via `GET /casal/status` (endpoint simples
a criar nesta tarefa, ver abaixo) e armazenado em signal.

### Novo endpoint `GET /casal/status`
- Autenticação: obrigatória
- Response 200: `{ "tem_parceiro": bool, "nome_parceiro": str | null }`
- Verifica `conexoes_casal` para o `usuario_id` autenticado
- Já usado pelo `WidgetParceiroComponent` (tarefa 09) — pode ser aproveitado

### Badge visual no item "Lançamentos"
- `pendentesCount > 0` e `temParceiro = true` → badge vermelho `#ef4444` sobre o ícone
- Número exibido; se `> 9` exibe `"9+"`
- Badge posicionado no canto superior direito do ícone com `position: absolute`

### Avatar no rodapé da sidebar
- Círculo de 32×32px com as iniciais do usuário (1 ou 2 letras, primeiras de cada palavra do nome)
- Cor de fundo: derivada de `parseInt(id.substring(0, 6), 16) % palette.length` onde `palette`
  é um array de 8 cores predefinidas em tokens do design system
- Exibido ao lado do link/botão de logout na parte inferior da sidebar

---

## 2. Ícones de forma de pagamento

### Constante compartilhada
Arquivo: `web/src/app/shared/constants/icones-pagamento.ts`

| `forma_pagamento` | Ícone (ng-icons heroicons) | Cor |
|---|---|---|
| `dinheiro` | `heroBanknotes` | `#22c55e` |
| `pix` | `heroQrCode` | `#32bcad` |
| `transferencia` | `heroArrowsRightLeft` | `#3ba6f1` |
| `cartao_credito` | `heroCreditCard` | `#8a05be` |
| `cartao_debito` | `heroCreditCard` | `#3b82f6` |
| `boleto` | `heroDocumentText` | `#f59e0b` |
| `deposito` | `heroBuildingLibrary` | `#78716c` |
| `outro` | `heroEllipsisHorizontal` | `#78716c` |

Fallback para forma nula ou desconhecida: `heroEllipsisHorizontal` + cor `#78716c`

### Componente reutilizável `IconePagamentoComponent`

Arquivo: `web/src/app/shared/components/icone-pagamento/icone-pagamento.component.ts`

- Input `forma: string`
- Renderiza o ícone mapeado na cor correspondente
- Tamanho padrão 16×16px; aceita Input `tamanho` para override

### Onde aplicar

| Local | Contexto |
|---|---|
| `ModalCriarDespesaComponent` | Cada opção do select de `forma_pagamento` exibe `IconePagamentoComponent` + rótulo PT-BR |
| `ModalCriarReceitaComponent` | Idem para `forma_recebimento` |
| `LancamentosComponent` | Cada item da lista exibe o ícone à esquerda do valor |
| `LancamentosRecentesComponent` | Widget do painel — mesmo ícone nos 8 itens recentes |

---

## 3. Modal de calculadora

### Comportamento geral
- O campo `valor` em ambos os modais (`ModalCriarDespesaComponent` e `ModalCriarReceitaComponent`)
  ganha um botão `heroCalculator` à direita
- Clique no botão abre `CalculadoraModalComponent` como overlay sobre o modal existente
- O display é pré-preenchido com o valor atual do campo (se já houver um)
- Ao clicar "Confirmar" (resultado válido), o modal fecha e o campo `valor` recebe o resultado
- Ao cancelar, o campo `valor` não é alterado

### Layout visual

```
┌────────────────────────────────┐
│  180 + 20                      │  ← display: expressão digitada
│  = 200,00                      │  ← resultado em tempo real
├───────┬───────┬───────┬────────┤
│   7   │   8   │   9   │   ÷    │
│   4   │   5   │   6   │   ×    │
│   1   │   2   │   3   │   −    │
│   0   │   ,   │   ⌫   │   +    │
├───────────────────────┬────────┤
│      Confirmar        │   C    │
└───────────────────────┴────────┘
```

- Largura máxima: 280px; centralizado na tela
- Botões numéricos: fundo `#ffffff`, borda `#e8e6e5`
- Botões de operador: fundo `rgba(59,166,241,0.08)`, texto `#3ba6f1`
- Botão "Confirmar": fundo `#3ba6f1`, texto branco; desabilitado se resultado inválido
- Botão "C": fundo `rgba(239,68,68,0.08)`, texto `#ef4444`

### Regras de negócio

- Operações suportadas: `+`, `−`, `×`, `÷` (internamente mapeadas para `+`, `-`, `*`, `/`)
- Separador decimal: vírgula (`,`) — convertida para ponto antes de avaliar
- Resultado arredondado para 2 casas decimais
- **Divisão por zero** → exibe `"Erro"` no display, botão Confirmar desabilitado
- **Resultado negativo** → botão Confirmar desabilitado (lançamentos têm valor positivo)
- **Expressão máxima:** 50 caracteres
- Botão `C` limpa a expressão inteira
- Botão `⌫` remove o último caractere da expressão
- Avaliação segura: antes de chamar `Function('return ' + expr)()`, sanitizar a expressão
  permitindo apenas dígitos, operadores `+`, `-`, `*`, `/`, ponto e espaço — qualquer outro
  caractere bloqueia a avaliação e exibe `"Erro"`

### Interface do componente

`web/src/app/shared/components/calculadora-modal/calculadora-modal.component.ts`

- Input `valorInicial: number` — pré-preenche o display
- Output `valorConfirmado: EventEmitter<number>` — emite o resultado ao confirmar
- Output `cancelado: EventEmitter<void>` — emite ao cancelar

---

## Novos arquivos

```
web/src/app/shared/
  constants/
    icones-pagamento.ts
  components/
    icone-pagamento/
      icone-pagamento.component.ts
      icone-pagamento.component.html
      icone-pagamento.component.scss
    calculadora-modal/
      calculadora-modal.component.ts
      calculadora-modal.component.html
      calculadora-modal.component.scss
```

## Componentes existentes a atualizar

| Componente | Mudança |
|---|---|
| `NavLateralComponent` | badge de pendentes + avatar com iniciais |
| `NavMobileComponent` | badge de pendentes |
| `ModalCriarDespesaComponent` | botão calculadora + `IconePagamentoComponent` no select |
| `ModalCriarReceitaComponent` | botão calculadora + `IconePagamentoComponent` no select |
| `LancamentosComponent` | `IconePagamentoComponent` em cada item da lista |
| `LancamentosRecentesComponent` | `IconePagamentoComponent` nos 8 itens recentes |
| `AuthService` | método `temParceiro()` via signal |

## Novo endpoint backend (pequeno, sem tabela)

**`GET /casal/status`**
- Autenticação: obrigatória
- Verifica `conexoes_casal` para o usuário autenticado
- Response 200: `{ "tem_parceiro": bool, "nome_parceiro": str | null }`
- Adicionar ao `api/app/routers/convites.py` (ou criar `api/app/routers/casal.py`)

---

## Verificação

```bash
# 1. Status de casal (sem parceiro)
curl -s http://localhost:8000/casal/status -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: { "tem_parceiro": false, "nome_parceiro": null }

# 2. Status de casal (com parceiro conectado)
# esperado: { "tem_parceiro": true, "nome_parceiro": "Maria" }
```

Frontend:
- Abrir `/painel` → sidebar sem badge (sem pendentes)
- Parceiro A cria lançamento → badge vermelho com `"1"` aparece na sidebar do usuário B ≤30s depois
- Badge muda para `"9+"` se contagem > 9
- Badge desaparece ao aceitar/ignorar todos os pendentes
- Avatar no rodapé exibe iniciais corretas (ex.: "João Silva" → "JS")
- Cor do avatar é consistente entre reloads e sessões diferentes
- Modal de despesa → select de `forma_pagamento` exibe ícones coloridos ao lado de cada rótulo
- Modal de receita → idem para `forma_recebimento`
- Clicar `heroCalculator` ao lado do campo `valor` → modal de calculadora abre
- Digitar `"150 + 30"` → display mostra `"150 + 30 = 180,00"`
- Clicar Confirmar → campo `valor` recebe `180.00`, modal fecha
- Digitar `"100 / 0"` → display mostra `"Erro"`, botão Confirmar desabilitado
- Resultado negativo → botão Confirmar desabilitado
- Lista `/lancamentos` → cada item exibe ícone com cor da forma de pagamento

---

## Fora do escopo

- Calculadora científica ou funções avançadas (%, raiz, etc.)
- Histórico de cálculos
- Ícones de bandeira de cartão (Visa, Mastercard, Elo) por enquanto
- Dark mode para os novos componentes (segue tokens CSS globais do `--color-*` já definidos)
- Notificação push de pendentes (além do polling de 30 segundos)
