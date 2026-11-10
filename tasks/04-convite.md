# Tarefa 04 — Sistema de Convite e Conexão do Casal

## Contexto

Permite que um usuário autenticado convide outra pessoa para o CasalEconomia. O convidado
abre um link único, cadastra apenas a senha (nome e e-mail já vêm pré-preenchidos), e as
duas pessoas ficam vinculadas. Cada uma mantém carteira própria e, quando conectadas, podem
visualizar e aceitar lançamentos uma da outra (funcionalidade das próximas tarefas).

**Pré-requisito:** tarefas 01, 02 e 03 concluídas.

---

## Tabelas a criar

### `convites`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `token` | UUID | sim | único, índice, gerado automaticamente |
| `nome_convidado` | VARCHAR(100) | sim | |
| `email_convidado` | VARCHAR(255) | sim | |
| `remetente_id` | UUID FK → `users.id` CASCADE | sim | quem enviou o convite |
| `usado_em` | TIMESTAMPTZ | não | nulo = pendente; preenchido ao aceitar |
| `criado_em` | TIMESTAMPTZ | sim | |

### `conexoes_casal`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `usuario_id_1` | UUID FK → `users.id` CASCADE | sim | sem hierarquia entre os dois |
| `usuario_id_2` | UUID FK → `users.id` CASCADE | sim | |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Endpoints

### `POST /convites`
- Autenticação: obrigatória
- Body: `nome_convidado` (string), `email_convidado` (email)
- Response 201: `{ token, nome_convidado, email_convidado }`
- Erros:
  - 400 se remetente já tem conexão ativa
  - 400 se e-mail convidado já está cadastrado
  - 400 se já existe convite pendente para esse e-mail
- O frontend monta o link: `window.location.origin + "/convite/" + token`

### `GET /convites/{token}`
- Autenticação: nenhuma (pública)
- Response 200: `{ nome, email }` (dados pré-preenchidos)
- Erros: 404 se token não existe, 410 se já foi usado

### `POST /convites/{token}/aceitar`
- Autenticação: nenhuma (pública)
- Body: `senha` (string, mín. 4 chars)
- Response 201: `{ mensagem: "Conta criada com sucesso. Faça login para continuar." }`
- Comportamento: cria usuário com nome+email do convite + senha informada → cria `conexoes_casal` → marca `usado_em`
- Erros: 404 token inválido, 410 já usado, 400 e-mail já cadastrado

---

## Regras de negócio

- Uma pessoa pode ter no máximo **uma** conexão de casal ativa
- O link é de **uso único** — `usado_em` preenchido invalida o token para sempre
- Após aceitar, o usuário é redirecionado para `/login` (sem auto-login)

---

## Frontend

### Tela `Configurações > Pessoas` (`/configuracoes/pessoas`)
- Formulário: campos `Nome` e `E-mail` do convidado
- Botão "Gerar link de convite"
- Após sucesso: exibe o link gerado (input somente leitura + botão "Copiar")
- Mensagem de erro em PT-BR para cada caso de rejeição da API
- Dica: "Link de uso único — expira após o cadastro"

### Tela pública `/convite/:token`
- Fora do AppShell (não exige login)
- Ao carregar: `GET /convites/{token}` → pré-preenche nome e e-mail (somente leitura)
- Campo editável: somente `Senha`
- Botão "Criar minha conta"
- Erros tratados: 404 → "Convite inválido", 410 → "Convite já utilizado"
- Após sucesso: redireciona para `/login?cadastro=sucesso`

### Tela de Login (atualizar tarefa 02)
- Exibir mensagem verde quando query param `cadastro=sucesso` estiver presente

---

## Verificação

```bash
# 1. Criar convite (autenticado)
curl -s -X POST http://localhost:8000/convites \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome_convidado":"Maria","email_convidado":"maria@teste.com"}' | python3 -m json.tool
# esperado: token UUID

TOKEN_CONVITE=<token-retornado>

# 2. Buscar dados do convite (público)
curl -s http://localhost:8000/convites/$TOKEN_CONVITE | python3 -m json.tool
# esperado: {"nome":"Maria","email":"maria@teste.com"}

# 3. Aceitar
curl -s -X POST http://localhost:8000/convites/$TOKEN_CONVITE/aceitar \
  -H "Content-Type: application/json" \
  -d '{"senha":"1234"}' | python3 -m json.tool
# esperado: mensagem de sucesso

# 4. Reutilizar token → 410
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8000/convites/$TOKEN_CONVITE/aceitar \
  -H "Content-Type: application/json" \
  -d '{"senha":"1234"}'
# esperado: 410
```

Frontend: abrir link `/convite/<token>` → nome e e-mail pré-preenchidos → preencher senha → cadastrar → redireciona para `/login` com mensagem verde.

---

## Fora do escopo

- Reenviar ou cancelar convite
- Expiração automática por tempo
- Desconectar um casal
- Notificação por e-mail
- Tela de Configurações > Casal mostrando dados do parceiro
