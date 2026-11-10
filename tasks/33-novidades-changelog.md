# T33 — Novidades in-app / Changelog

## Objetivo
Comunicar aos usuários as novas funcionalidades e correções de cada versão do sistema diretamente
dentro do app, sem precisar sair para um blog ou repositório externo.

---

## Contexto e motivação
Quando uma funcionalidade nova é lançada (ex.: busca global, orçamento mensal), o usuário pode
não perceber. Com o painel de novidades, cada release tem um resumo amigável de "o que há de novo",
acessível a qualquer momento e com destaque automático quando há conteúdo novo ainda não visto.

---

## Nova tabela: `versoes`

| Coluna         | Tipo        | Descrição                                              |
| -------------- | ----------- | ------------------------------------------------------ |
| `id`           | UUID PK     |                                                        |
| `versao`       | texto       | Ex.: `0.17.0`                                          |
| `titulo`       | texto       | Ex.: _"Orçamento mensal e busca global"_               |
| `resumo`       | texto       | Texto curto (máx. 200 chars) para o card na lista      |
| `corpo`        | texto       | Markdown com o detalhamento completo das novidades     |
| `publicado_em` | date        | Data de publicação                                     |
| `criado_em`    | timestamptz |                                                        |

### Tabela: `versoes_vistas`

| Coluna       | Tipo        | Descrição                     |
| ------------ | ----------- | ----------------------------- |
| `usuario_id` | FK PK       |                               |
| `versao_id`  | FK PK       |                               |
| `visto_em`   | timestamptz |                               |

---

## Fluxo do usuário

1. Ao abrir o app após uma nova versão, aparece um badge vermelho no ícone de novidades
   (sino ou estrela) na barra lateral.
2. Ao clicar: painel lateral (drawer) com a lista de versões em ordem decrescente.
3. A versão mais recente aparece expandida com o corpo completo em Markdown.
4. As demais versões aparecem como cards compactos (título + resumo + data).
5. Clicar em um card expande o corpo completo.
6. Fechar o drawer registra todas as versões exibidas como "vistas" para o usuário.
7. Badge some após fechar.

---

## Painel do admin

- Rota `/admin/novidades` (restrita a administrador).
- Formulário para criar/editar versão: versão, título, resumo, corpo (editor Markdown com preview),
  data de publicação.
- Versões com `publicado_em` futuro não aparecem para usuários comuns (pré-agendamento).
- Botão **"Enviar e-mail para todos"**: dispara e-mail com o resumo da versão para todos os
  usuários ativos.

---

## Endpoints

| Método | Rota                            | Quem acessa   | Ação                                      |
| ------ | ------------------------------- | ------------- | ----------------------------------------- |
| GET    | `/novidades`                    | Usuário autenticado | Lista versões publicadas + flag `vista`  |
| POST   | `/novidades/{id}/marcar-vista`  | Usuário autenticado | Marca versão como vista                  |
| GET    | `/novidades/contagem-novas`     | Usuário autenticado | Número de versões não vistas             |
| GET    | `/admin/novidades`              | Admin         | Lista todas (incluindo futuras)           |
| POST   | `/admin/novidades`              | Admin         | Cria nova versão                          |
| PUT    | `/admin/novidades/{id}`         | Admin         | Edita versão                              |
| DELETE | `/admin/novidades/{id}`         | Admin         | Remove (somente se não publicada ainda)   |
| POST   | `/admin/novidades/{id}/enviar-email` | Admin   | Envia e-mail para todos usuários ativos   |

---

## E-mail de novidades

- Assunto: _"🚀 Casal Economia {versao} — {titulo}"_
- Corpo: resumo + link para abrir o app.
- Enviado apenas para usuários com `notificacoes_email = true` (T19).
- Rate limit: 1 envio por versão (evitar reenvios acidentais).

---

## Regras de negócio

1. `publicado_em` nulo ou futuro: visível apenas para admin.
2. Badge de novidades: contagem de versões `publicado_em <= hoje` não vistas pelo usuário.
3. Marcar como vista é idempotente (segunda chamada não gera erro).
4. Excluir versão só é permitido se `publicado_em` for futuro ou nulo (versões já publicadas
   são imutáveis para garantir histórico confiável).
5. O e-mail de novidades nunca é enviado automaticamente — sempre ação deliberada do admin.
6. Markdown no corpo suporta: títulos H2/H3, listas, negrito, itálico, código inline e links.
   Sem HTML raw, sem imagens por URL externa.

---

## Verificação

```
# Verificar contagem de novas versões
curl -s http://localhost:8000/api/novidades/contagem-novas \
  -H "Cookie: session=..." | jq '.data.contagem'
# → 1 (se houver versão nova não vista)

# Listar versões
curl -s http://localhost:8000/api/novidades \
  -H "Cookie: session=..." | jq '.data[0].vista'
# → false (primeira vez)

# Marcar como vista
curl -s -X POST http://localhost:8000/api/novidades/<id>/marcar-vista \
  -H "Cookie: session=..."

# Verificar que contagem voltou a zero
curl -s http://localhost:8000/api/novidades/contagem-novas \
  -H "Cookie: session=..." | jq '.data.contagem'
# → 0

# Admin: criar versão futura (não deve aparecer para usuário comum)
curl -s -X POST http://localhost:8000/api/admin/novidades \
  -H "Content-Type: application/json" -H "Cookie: admin_session=..." \
  -d '{"versao":"0.18.0","titulo":"Rascunho","resumo":"...","corpo":"...","publicado_em":"2027-01-01"}' | jq '.data.id'
# Admin vê; usuário não vê em GET /novidades
```

---

## Fora de escopo

- Push notifications para novidades (além do badge in-app e e-mail).
- Comentários de usuários em cada versão.
- Versões com múltiplos idiomas.
- Feed RSS público do changelog.
