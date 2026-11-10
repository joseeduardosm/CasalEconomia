# Tarefa 02 — Autenticação (Login e Cadastro)

## Contexto

Implementa registro e login de usuários com JWT. O token é armazenado no `localStorage`
do navegador e enviado em todas as requisições autenticadas via cabeçalho `Authorization: Bearer`.

**Pré-requisito:** tarefa 01 concluída.

---

## Tabela: `users`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | `default=uuid4` |
| `name` | VARCHAR(100) | sim | |
| `email` | VARCHAR(255) | sim | único, índice |
| `hashed_password` | VARCHAR(255) | sim | bcrypt via `passlib[bcrypt]` |
| `criado_em` | TIMESTAMPTZ | sim | `default=now()` |

Adicionar ao `requirements.txt`:
- `passlib[bcrypt]==1.7.4`
- `python-jose[cryptography]==3.3.0`

---

## Endpoints

### `POST /auth/register`
- Autenticação: nenhuma
- Body: `name` (string), `email` (email), `password` (string, mín. 4 chars)
- Response 201: `{ access_token, token_type: "bearer" }`
- Erros: 400 se e-mail já cadastrado
- Comportamento: hash da senha com bcrypt, cria usuário, retorna token JWT

### `POST /auth/login`
- Autenticação: nenhuma
- Body: `email`, `password`
- Response 200: `{ access_token, token_type: "bearer" }`
- Erros: 401 se credenciais inválidas
- Comportamento: busca usuário por email, verifica hash, retorna token

---

## Token JWT

| Propriedade | Valor |
|---|---|
| Payload | `{ "sub": "<user_uuid>", "exp": <agora + 7 dias> }` |
| Algoritmo | HS256 |
| Chave | `SECRET_KEY` do `.env` |

---

## Repositório `users`

Funções necessárias:
- `find_by_email(db, email)` → User ou None
- `create(db, name, email, hashed_password)` → User

---

## Extração do usuário autenticado

Todos os routers que requerem autenticação devem ter uma função `_obter_usuario_atual(authorization: str = Header(...)) -> uuid.UUID` que decodifica o JWT e retorna o ID do usuário. Essa função será duplicada por enquanto — uma tarefa futura centralizará em um middleware compartilhado.

---

## Frontend

### Tela de Login (`/login`)
- Campos: e-mail, senha
- Submit: `POST /auth/login` → salva token no `localStorage` → navega para `/painel`
- Link para `/cadastro`
- Mensagem de erro em PT-BR quando credenciais inválidas
- Exibe mensagem verde quando query param `cadastro=sucesso` estiver presente (vindo do fluxo de convite — tarefa 04)

### Tela de Cadastro (`/cadastro`)
- Campos: nome, e-mail, senha
- Submit: `POST /auth/register` → salva token → navega para `/painel`
- Link para `/login`
- Mensagem de erro em PT-BR quando e-mail já existe

### `AuthService` (singleton, `providedIn: 'root'`)
- Métodos: `salvarToken(token)`, `getToken()`, `estaAutenticado()`, `sair()`
- Armazena token no `localStorage`
- `sair()` remove token e navega para `/login`

### `authInterceptor` (interceptor funcional)
- Injeta `Authorization: Bearer <token>` em toda requisição quando autenticado

### `authGuard` (guard funcional)
- Redireciona para `/login` se `AuthService.estaAutenticado()` retornar false
- Aplicado em todas as rotas protegidas (configurado na tarefa 03)

### Design (Seline Analytics)
- Canvas: `#fafaf9`, card: `#ffffff`, borda: `#e8e6e5`, CTA: `#3ba6f1`
- Card centralizado, largura máx. 440px, fundo canvas
- Label "CasalEconomia" em destaque no topo do card

---

## Verificação

```bash
# Cadastrar
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"João","email":"joao@teste.com","password":"1234"}' | python3 -m json.tool
# esperado: access_token

# Login
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@teste.com","password":"1234"}' | python3 -m json.tool
# esperado: access_token

# E-mail duplicado → 400
# Senha errada → 401
```

Frontend: acessar `/login`, fazer login → confirmar navegação para `/painel`.
Acessar `/painel` sem login → redireciona para `/login`.

---

## Fora do escopo

- Refresh token
- Recuperação de senha
- Autenticação social
- Verificação de e-mail
