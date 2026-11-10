# Tarefa 19 — Configurações do Usuário

## Contexto

Implementa a tela `/configuracoes` (já presente como placeholder na navegação desde a tarefa 03)
com quatro seções: perfil do usuário, segurança, preferências de exibição e gerenciamento do
vínculo de casal (desconexão).

Sem novas tabelas: todas as informações vivem em campos já existentes em `users` ou em nova
coluna de preferências na mesma tabela.

**Pré-requisito:** tarefas 01–18 concluídas.

---

## Novas colunas em `users`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `tema` | VARCHAR(10) | sim | `claro` / `escuro` / `sistema` — default `sistema` |
| `moeda` | VARCHAR(5) | sim | código ISO ex: `BRL` — default `BRL` |
| `formato_data` | VARCHAR(12) | sim | `dd/MM/yyyy` / `MM/dd/yyyy` — default `dd/MM/yyyy` |
| `notificacoes_email` | BOOLEAN | sim | default `true` |

---

## Seções da tela de configurações

### Seção A — Perfil

Campos editáveis do usuário autenticado:
- **Nome completo** (`name`)
- **E-mail** (`email`) — edição exige confirmação de senha atual
- **Foto de perfil** — upload de imagem (máx 2 MB, MIME: image/png, image/jpeg);
  armazenada no bucket S3 privado (mesma infra da tarefa 23 de anexos);
  exibida no avatar da sidebar (tarefa 10) em vez das iniciais
- Botão "Salvar alterações de perfil"

### Seção B — Segurança

- **Trocar senha**: campos `senha_atual`, `nova_senha`, `confirmar_nova_senha`
- Regra: `nova_senha` ≥ 8 caracteres, pelo menos uma letra maiúscula e um dígito
- Não exibir nenhum valor de senha preenchido; sempre em branco ao abrir
- Botão "Alterar senha"
- **Sessões ativas**: lista de sessões abertas (data, dispositivo/user-agent simplificado);
  botão "Encerrar todas as outras sessões"
- **Excluir conta**: botão destrutivo com modal de confirmação;
  requer digitar o e-mail do usuário para confirmar;
  exclusão remove todos os dados (cascade no banco) após confirmação

### Seção C — Preferências de exibição

- **Tema**: radio com opções Claro / Escuro / Seguir sistema
  Ao selecionar, aplica imediatamente sem recarregar a página (via atributo `data-theme` no `<html>`)
- **Moeda**: select (BRL, USD, EUR — lista curta para MVP)
- **Formato de data**: radio com exemplos `09/11/2026` ou `11/09/2026`
- Salvo no backend via `PATCH /configuracoes`; lido no carregamento da sessão
- Botão "Salvar preferências"

### Seção D — Vínculo de casal

Visível apenas se o usuário tiver parceiro conectado (`tem_parceiro = true`).

- Exibe nome e e-mail do parceiro atual
- **Botão "Desconectar do casal"**: abre modal de confirmação explicando que
  lançamentos compartilhados permanecem no histórico mas novos compartilhamentos
  deixarão de ser possíveis; `conexoes_casal` marcada como inativa

Visível apenas se não tiver parceiro:
- Link para a tela de convite (tarefa 04) "Convidar parceiro"

### Seção E — Categorias personalizadas

Atalho para a sub-tela `/configuracoes/categorias` (tarefa 17).
Exibe contagem de categorias criadas e botão "Gerenciar categorias".

---

## Endpoints

### `GET /me`
- Autenticação: obrigatória
- Response 200: dados do usuário autenticado (nome, email, tema, moeda, formato_data,
  notificacoes_email, foto_url, tem_parceiro, nome_parceiro)

### `PATCH /configuracoes/perfil`
- Autenticação: obrigatória
- Body: `nome` (opt), `email` (opt) — se email: exige `senha_atual`
- Response 200: usuário atualizado

### `POST /configuracoes/foto`
- Autenticação: obrigatória
- Multipart form com campo `foto` (imagem, máx 2 MB)
- Valida MIME e tamanho; faz upload para S3; salva URL em `users.foto_url`
- Response 200: `{ "foto_url": "https://..." }`

### `PATCH /configuracoes/senha`
- Autenticação: obrigatória
- Body: `senha_atual`, `nova_senha`, `confirmar_nova_senha`
- Response 200: senha atualizada; todas as outras sessões do usuário invalidadas

### `PATCH /configuracoes/preferencias`
- Autenticação: obrigatória
- Body: `tema`, `moeda`, `formato_data`, `notificacoes_email`
- Response 200: preferências atualizadas

### `GET /configuracoes/sessoes`
- Autenticação: obrigatória
- Response 200: lista de sessões ativas com data_criacao, user_agent simplificado, ip (ocultado)

### `DELETE /configuracoes/sessoes`
- Autenticação: obrigatória
- Encerra todas as sessões EXCETO a corrente
- Response 200

### `DELETE /casal/conexao`
- Autenticação: obrigatória
- Desconecta o usuário do casal; parceiro também perde o vínculo
- Response 200: `{ "desconectado": true }`

### `DELETE /me`
- Autenticação: obrigatória
- Body: `email_confirmacao` — deve ser igual ao email do usuário autenticado
- Exclusão em cascata (users, lancamentos, contas, cartoes, metas, categorias, etc.)
- Response 200: confirmação; token invalidado

---

## Frontend

### Tela `/configuracoes`

Substituir placeholder. Navegação por abas verticais (desktop) ou abas horizontais scrolláveis
(mobile):
- Aba "Perfil"
- Aba "Segurança"
- Aba "Preferências"
- Aba "Casal"
- Aba "Categorias" (atalho para `/configuracoes/categorias`)

### Comportamento de tema

- Ao selecionar tema, `document.documentElement.setAttribute('data-theme', tema)` imediato
- Valor salvo no backend via `PATCH /configuracoes/preferencias` ao clicar "Salvar"
- No carregamento da app: ler `tema` do `GET /me` e aplicar antes de renderizar conteúdo

### Upload de foto de perfil

- Input `<file>` oculto acionado pelo clique no avatar da sidebar
- Preview antes de confirmar (FileReader API)
- Depois do upload: avatar da sidebar atualiza sem recarregar a página

### Modal de desconexão do casal

- Título: "Desconectar do casal"
- Texto: "Você e [nome parceiro] deixarão de compartilhar lançamentos. O histórico anterior
  não é excluído. Esta ação não pode ser desfeita facilmente."
- Input de confirmação: "Digite o e-mail do parceiro para confirmar"
- Botão vermelho "Desconectar"

### Modal de exclusão de conta

- Input de confirmação: "Digite seu e-mail ([email]) para confirmar"
- Botão vermelho "Excluir minha conta"
- Após exclusão: redirecionar para `/login`

### `ConfiguracoesService` (Angular, singleton)

Métodos: `carregarPerfil()`, `atualizarPerfil(dados)`, `uploadFoto(file)`,
`alterarSenha(dados)`, `atualizarPreferencias(dados)`, `listarSessoes()`,
`encerrarOutrasSessoes()`, `desconectarCasal()`, `excluirConta(email)`

---

## Verificação

```bash
# 1. Buscar configurações do usuário
curl -s http://localhost:8000/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: nome, email, tema, moeda, formato_data, tem_parceiro

# 2. Atualizar nome
curl -s -X PATCH http://localhost:8000/configuracoes/perfil \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome":"José Eduardo"}' | python3 -m json.tool
# esperado: 200 com nome atualizado

# 3. Trocar senha
curl -s -X PATCH http://localhost:8000/configuracoes/senha \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"senha_atual":"Atual123","nova_senha":"Nova123!","confirmar_nova_senha":"Nova123!"}' \
  | python3 -m json.tool
# esperado: 200; outros tokens invalidados

# 4. Senha antiga incorreta → 401

# 5. Trocar tema para escuro
curl -s -X PATCH http://localhost:8000/configuracoes/preferencias \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"tema":"escuro"}' | python3 -m json.tool

# 6. Desconectar casal
curl -s -X DELETE http://localhost:8000/casal/conexao \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: 200; GET /me mostra tem_parceiro=false

# 7. Verificar que parceiro também perdeu o vínculo
curl -s http://localhost:8000/me -H "Authorization: Bearer $TOKEN_PARCEIRO" | python3 -m json.tool
# esperado: tem_parceiro=false
```

Frontend:
- Abrir `/configuracoes` → aba "Perfil" ativa por padrão
- Editar nome → salvar → sidebar atualiza com novo nome no avatar
- Trocar tema para Escuro → app muda imediatamente; aba Preferências salva
- Aba "Segurança" → trocar senha → logout automático em outras abas do browser
- Aba "Casal" → desconectar → aba some; link "Convidar parceiro" aparece

---

## Fora do escopo

- Autenticação social (Google, Apple)
- 2FA / MFA
- Exportação completa de dados (GDPR export)
- Múltiplos idiomas (apenas PT-BR no MVP)
- Notificações push / email configuradas por tipo específico
- Histórico de alterações de perfil
