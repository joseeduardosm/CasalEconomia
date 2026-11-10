# Tarefa 20 — Central de Notificações In-App

## Contexto

Implementa um centro de notificações persistente acessível pelo ícone de sino no topo da
interface. Consolida eventos relevantes que hoje ficam invisíveis ao usuário: lançamento
compartilhado aceito/ignorado pelo parceiro, fatura vencendo em breve, meta atingida ou em
risco, fechamento do casal registrado ou quitado.

Sem push notification. Funciona por polling ao abrir o sino e por atualização no carregamento
de cada tela relevante.

**Pré-requisito:** tarefas 01–19 concluídas. Requer tarefas 05 (sincronizador), 06 (cartões),
13 (casal), 14 (metas).

---

## Nova tabela

### `notificacoes`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | destinatário |
| `tipo` | VARCHAR(50) | sim | ver tabela de tipos abaixo |
| `titulo` | VARCHAR(120) | sim | texto curto exibido no item |
| `corpo` | VARCHAR(400) | não | texto complementar (opcional) |
| `link` | VARCHAR(200) | não | rota para navegar ao clicar (ex: `/lancamentos`) |
| `lida` | BOOLEAN | sim | default `false` |
| `lida_em` | TIMESTAMPTZ | não | preenchido ao marcar como lida |
| `dado_id` | UUID | não | ID do objeto relacionado (lançamento, meta, etc.) |
| `dado_tipo` | VARCHAR(40) | não | tipo do objeto (`lancamento`, `meta`, `fechamento`, `fatura`) |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Tipos de notificação

| `tipo` | Gatilho | Quem cria |
|---|---|---|
| `lancamento_compartilhado_aceito` | Parceiro aceita lançamento enviado | Service ao processar aceitação |
| `lancamento_compartilhado_ignorado` | Parceiro ignora lançamento enviado | Service ao processar ignorar |
| `lancamento_compartilhado_excluido` | Dono exclui lançamento já aceito pelo parceiro | Service ao excluir (já existe em T07) |
| `fatura_vencendo` | Fatura com vencimento em até 5 dias | Sincronizador diário |
| `meta_atingida` | Meta de economia chega a 100% | Sincronizador ou ao registrar contribuição |
| `meta_em_risco` | Meta de economia com data_fim ≤ 30 dias e progresso < 70% | Sincronizador diário |
| `meta_limite_atencao` | Meta de limite_gasto atinge 80% | Service ao criar/editar lançamento |
| `meta_limite_estourado` | Meta de limite_gasto ultrapassa 100% | Service ao criar/editar lançamento |
| `fechamento_registrado` | Parceiro registra um fechamento do casal | Service ao criar fechamento |
| `fechamento_quitado` | Parceiro marca fechamento como quitado | Service ao quitar |
| `convite_aceito` | Usuário convidado aceita o convite do casal | Service ao aceitar convite (T04) |

---

## Regras de negócio

### Criação de notificações

- Notificações são criadas pelos services de negócio como efeito colateral de ações do usuário
  ou do sincronizador — nunca pelo cliente diretamente
- Deduplicação: antes de criar, verificar se já existe notificação do mesmo `tipo` + `dado_id`
  nas últimas 24h para o mesmo `usuario_id`; se sim, não criar duplicata
- `fatura_vencendo`: criada pelo sincronizador uma vez por fatura, quando `data_vencimento` ≤ hoje + 5
  E `liquidado = false`; não repetir se já existe notificação para aquela fatura não lida

### Contagem de não lidas (badge no sino)

- Badge vermelho com número no ícone de sino quando há notificações com `lida = false`
- Contagem atualizada via polling de `GET /notificacoes/contagem` a cada 60s
  (mesmo mecanismo do badge de lançamentos pendentes da tarefa 10)

### Leitura e marcação

- Abrir o painel de notificações: `GET /notificacoes` (20 mais recentes, não lidas primeiro)
- Clicar em uma notificação: marca como lida (`PATCH /notificacoes/{id}/ler`) + navega para `link`
- Botão "Marcar todas como lidas": `PATCH /notificacoes/ler-todas`
- Notificações lidas ficam visíveis por 30 dias; expiradas são excluídas pelo sincronizador

### Retenção

- O sincronizador (tarefa 05) executa limpeza semanal: exclui notificações com `lida = true`
  e `lida_em < hoje - 30 dias`
- Notificações não lidas nunca são excluídas automaticamente

---

## Endpoints

### `GET /notificacoes/contagem`
- Autenticação: obrigatória
- Response 200: `{ "nao_lidas": N }`
- Usado para o badge do sino; chamada leve (apenas COUNT)

### `GET /notificacoes`
- Autenticação: obrigatória
- Query params: `pagina` (int, default 1), `por_pagina` (int, default 20), `apenas_nao_lidas` (bool)
- Response 200: lista paginada com total e `tem_mais: bool`

### `PATCH /notificacoes/{id}/ler`
- Autenticação: obrigatória
- Verifica que a notificação pertence ao usuário autenticado
- Response 200: notificação marcada como lida

### `PATCH /notificacoes/ler-todas`
- Autenticação: obrigatória
- Marca todas as notificações do usuário como lidas
- Response 200: `{ "marcadas": N }`

### `DELETE /notificacoes/{id}`
- Autenticação: obrigatória
- Remove uma notificação específica
- Response 200

---

## Frontend

### Ícone de sino na barra de topo (`BarraTopoComponent` ou `NavLateralComponent`)

- Ícone `heroBell` com badge vermelho numérico quando `nao_lidas > 0`
- Badge mostra "9+" se `nao_lidas > 9`
- Polling de `GET /notificacoes/contagem` a cada 60s via `setInterval`
- Polling iniciado em `AppComponent.ngOnInit`, limpo em `ngOnDestroy`

### Painel de notificações (dropdown/drawer)

Abre ao clicar no sino:

- Cabeçalho: "Notificações" + botão "Marcar todas como lidas" (visível se há não lidas)
- Lista de notificações:
  - Ícone do tipo (definido em `ICONES_NOTIFICACAO` — constante em `shared/constants/`)
  - Título + corpo (truncado em 2 linhas)
  - Tempo relativo: "há 5 min", "há 2 h", "ontem" (sem biblioteca de datas — calcular manualmente)
  - Fundo levemente destacado para não lidas
  - Clique: marca como lida + navega para `link`
- Rodapé: link "Ver todas" se tiver paginação
- Estado vazio: "Nenhuma notificação" com ícone
- Botão fechar (×) ou clique fora fecha o painel

### `NotificacoesService` (Angular, singleton)

Métodos: `contagem()`, `listar(params)`, `marcarLida(id)`, `marcarTodasLidas()`, `excluir(id)`

Mantém signal `contagem: Signal<number>` atualizado pelo polling.

---

## Verificação

```bash
# 1. Sem notificações → contagem=0
curl -s http://localhost:8000/notificacoes/contagem \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: { "nao_lidas": 0 }

# 2. Usuário A cria lançamento compartilhado com B
# Usuário B aceita → notificação criada para A
curl -s http://localhost:8000/notificacoes \
  -H "Authorization: Bearer $TOKEN_A" | python3 -m json.tool
# esperado: notificação tipo=lancamento_compartilhado_aceito

# 3. Marcar como lida
curl -s -X PATCH http://localhost:8000/notificacoes/$ID/ler \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lida=true, lida_em preenchido

# 4. Contagem volta a 0 após marcar todas

# 5. Sincronizador cria notificação de fatura vencendo
# criar fatura com data_vencimento = hoje + 3 dias
# executar rotina de sincronizador de notificações → verificar notificacao criada

# 6. Meta atingida
# meta de economia com valor_alvo=100; registrar contribuição de 100
# GET /notificacoes → notificação tipo=meta_atingida
```

Frontend:
- Sem notificações → sino sem badge
- Aceitar lançamento do parceiro → sino do usuário emissor ganha badge em até 60s
- Abrir sino → painel abre com a notificação; não lida com fundo destacado
- Clicar notificação → navega para rota e marca como lida
- Badge zera após "Marcar todas como lidas"

---

## Fora do escopo

- Push notifications (web push API)
- Notificações por e-mail por tipo específico (tarefa 19 tem toggle global)
- Notificações em tempo real via WebSocket
- Configuração por tipo de notificação (ativar/desativar individualmente)
- Notificações de relatório semanal automático
