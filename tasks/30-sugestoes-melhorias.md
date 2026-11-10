# T30 — Sugestões de melhorias in-app

## Objetivo
Permitir que qualquer usuário envie uma sugestão de melhoria diretamente do app, com screenshot
opcional, sem sair da tela onde está. O mantenedor recebe, triaga e pode responder ao autor.

---

## Contexto e motivação
Usuários têm ideias enquanto usam o app. Sem um canal direto, o feedback se perde em mensagens
informais. Com o botão flutuante, a sugestão chega com contexto (qual tela), screenshot opcional
e forma de resposta — tudo no mesmo lugar.

---

## Nova tabela: `sugestoes`

| Coluna              | Tipo        | Descrição                                                   |
| ------------------- | ----------- | ----------------------------------------------------------- |
| `id`                | UUID PK     |                                                             |
| `numero`            | int único   | Número público sequencial (#1, #2, …)                       |
| `usuario_id`        | FK nullable | Autor (null se conta foi excluída)                          |
| `usuario_nome`      | texto       | Nome no momento do envio (retrato)                          |
| `texto`             | texto       | Descrição da sugestão                                       |
| `tela`              | texto       | URL/rota de onde foi enviada                                |
| `situacao`          | texto       | `nova`, `em_analise`, `aceita`, `recusada`, `concluida`     |
| `resposta_publica`  | texto       | Resposta visível ao autor                                   |
| `criado_em`         | timestamptz |                                                             |
| `atualizado_em`     | timestamptz |                                                             |

### Tabela auxiliar: `sugestoes_eventos`

| Coluna         | Tipo        | Descrição                           |
| -------------- | ----------- | ----------------------------------- |
| `id`           | UUID PK     |                                     |
| `sugestao_id`  | FK          |                                     |
| `autor_nome`   | texto       |                                     |
| `acao`         | texto       | `situacao_alterada`, `respondido`   |
| `detalhe`      | texto       | Valor novo da situação ou trecho    |
| `criado_em`    | timestamptz |                                     |

---

## Fluxo do usuário comum

1. Usuário clica no botão flutuante **"Sugerir melhoria"** (canto inferior direito, todas as telas).
2. Abre drawer lateral com campo de texto e área de captura de screenshot.
3. Preenche a sugestão (mín. 10 caracteres, máx. 2000).
4. Screenshot é opcional: captura o estado atual da tela via `html2canvas` ou é enviada como
   upload de imagem (máx. 5 MB, tipos: image/png, image/jpeg, image/webp).
5. Envia → confirmação: _"Sugestão #12 enviada! Você pode acompanhá-la em Minhas sugestões."_
6. Em **Configurações → Minhas sugestões**: lista todas as sugestões do usuário com situação atual
   e resposta pública quando houver.

---

## Fluxo do mantenedor (admin)

- Rota `/admin/sugestoes` (restrita a administrador).
- Lista todas as sugestões ordenadas por data, com filtro por situação e tela.
- Cada sugestão pode ter situação alterada e resposta pública escrita.
- Ao responder, o usuário autor recebe notificação in-app (tipo `sugestao_respondida`) e e-mail
  com o texto da resposta.
- Situação `concluida` indica que a melhoria foi implementada.

---

## Endpoints

| Método | Rota                              | Quem acessa   | Ação                                    |
| ------ | --------------------------------- | ------------- | --------------------------------------- |
| POST   | `/sugestoes`                      | Usuário autenticado | Envia sugestão                   |
| GET    | `/sugestoes/minhas`               | Usuário autenticado | Lista as próprias sugestões      |
| GET    | `/admin/sugestoes`                | Admin         | Lista todas                             |
| GET    | `/admin/sugestoes/{id}`           | Admin         | Detalhe com eventos                     |
| PATCH  | `/admin/sugestoes/{id}`           | Admin         | Altera situação e/ou resposta pública   |

---

## Regras de negócio

1. Um usuário pode enviar no máximo 10 sugestões em 24 horas (rate limit por `usuario_id`).
2. Screenshot é opcional; se enviado, passa por validação de MIME e tamanho antes de ser aceito.
3. A URL/rota de origem é capturada automaticamente pelo frontend no momento de abertura do drawer.
4. Situação inicial sempre `nova`; só o admin pode avançar.
5. Resposta pública só aparece ao autor depois de salva (nunca rascunho parcial visível).
6. Ao excluir a conta, `usuario_id` vira null mas o `usuario_nome` permanece (retrato).

---

## UI — Telas afetadas

| Tela                        | Elemento                                                 |
| --------------------------- | -------------------------------------------------------- |
| Todas as telas              | Botão flutuante "Sugerir melhoria" (canto inferior dir.) |
| Configurações               | Aba "Minhas sugestões" com lista e status                |
| `/admin/sugestoes`          | Painel de triagem (somente admin)                        |

---

## Notificação ao autor

Ao receber resposta do admin, o autor recebe:
- Notificação in-app do tipo `sugestao_respondida` com link para "Minhas sugestões".
- E-mail com assunto _"Resposta à sua sugestão #12"_ e o texto da resposta pública.

---

## Verificação

```
# Enviar sugestão
curl -s -X POST http://localhost:8000/api/sugestoes \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"texto": "Gostaria de um modo escuro por padrão", "tela": "/painel"}' \
  | jq '.data.numero'
# → 1 (ou próximo número sequencial)

# Listar minhas sugestões
curl -s http://localhost:8000/api/sugestoes/minhas \
  -H "Cookie: session=..." | jq '.data[0].situacao'
# → "nova"

# Admin: alterar situação e responder
curl -s -X PATCH http://localhost:8000/api/admin/sugestoes/<id> \
  -H "Content-Type: application/json" -H "Cookie: admin_session=..." \
  -d '{"situacao": "aceita", "resposta_publica": "Ótima ideia, está no nosso roadmap!"}' \
  | jq '.data.situacao'
# → "aceita"
```

---

## Fora de escopo

- Upvote / curtir sugestões de outros usuários.
- Sugestões anônimas (sem login).
- Integração com GitHub Issues ou outro sistema externo de tarefas.
- Painel público de roadmap.
