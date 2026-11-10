# Tarefa 23 — Anexos em Lançamentos

## Contexto

Permite vincular arquivos (fotos de nota fiscal, comprovantes de pagamento, contratos) a um
lançamento. O usuário fotografa a nota ou faz print do comprovante e anexa ao lançamento para
consulta futura.

O upload segue o fluxo S3 assinado: o backend gera uma URL pré-assinada e o browser envia o
arquivo diretamente para o S3, sem trafegar pelo servidor da API — reduzindo latência e carga.

**Pré-requisito:** tarefas 01–22 concluídas. Requer infraestrutura S3 (ou compatível: MinIO
em desenvolvimento local, AWS S3 em produção).

**Dependências novas:** `boto3==1.34.0` (AWS SDK Python) para geração de URLs assinadas e
metadata de validação pós-upload.

---

## Nova tabela

### `anexos`

| Campo | Tipo | Obrigatório | Notas |
|---|---|---|---|
| `id` | UUID PK | sim | |
| `lancamento_id` | UUID FK → `lancamentos.id` CASCADE | sim | |
| `usuario_id` | UUID FK → `users.id` CASCADE | sim | quem fez o upload |
| `nome_original` | VARCHAR(260) | sim | nome do arquivo enviado pelo usuário |
| `nome_armazenamento` | VARCHAR(260) | sim | UUID gerado para o objeto no S3 |
| `mime_type` | VARCHAR(100) | sim | validado na geração da URL e confirmado no pós-upload |
| `tamanho_bytes` | BIGINT | não | preenchido na confirmação pós-upload |
| `url_thumbnail` | TEXT | não | gerada assincronamente para imagens |
| `upload_confirmado` | BOOLEAN | sim | default `false`; `true` após confirmação |
| `criado_em` | TIMESTAMPTZ | sim | |

---

## Regras de negócio

### Tipos de arquivo permitidos (whitelist de MIME)

- `image/jpeg`, `image/png`, `image/webp`, `image/heic`
- `application/pdf`
- `image/gif` (somente estático — validado no backend)

### Limites

- Tamanho máximo por arquivo: **10 MB**
- Número máximo de anexos por lançamento: **5**
- Bucket S3 é **privado** — arquivos não acessíveis diretamente por URL pública

### Fluxo de upload (3 etapas)

**Etapa 1 — Solicitar URL assinada (`POST /lancamentos/{id}/anexos/url-upload`):**
- Backend valida que o lançamento pertence ao usuário
- Valida MIME e tamanho informados no request
- Gera `nome_armazenamento` = UUID aleatório + extensão derivada do MIME
- Gera URL pré-assinada S3 PUT com expiração de 10 minutos
- Cria registro em `anexos` com `upload_confirmado = false`
- Retorna `{ "upload_url": str, "anexo_id": UUID }`

**Etapa 2 — Upload direto pelo browser:**
- O JavaScript faz `PUT` para a URL assinada com o arquivo e o cabeçalho `Content-Type`
- Nenhuma chamada para o backend nesta etapa

**Etapa 3 — Confirmar upload (`POST /lancamentos/{id}/anexos/{anexo_id}/confirmar`):**
- Backend faz `HEAD` no objeto S3 para verificar que existe e ler metadados (`Content-Type`, `Content-Length`)
- Valida MIME e tamanho reais (segundo fator de segurança)
- Atualiza `upload_confirmado = true`, `mime_type`, `tamanho_bytes`
- Se MIME for imagem: aciona geração assíncrona de thumbnail (via APScheduler ou task queue simples)
- Retorna o anexo confirmado

### Acesso aos arquivos (URL de download)

Arquivos não têm URL pública. Para visualizar ou baixar:
- Backend gera URL S3 pré-assinada GET com expiração de 15 minutos via
  `GET /lancamentos/{id}/anexos/{anexo_id}/url-download`
- Frontend recebe a URL e abre em nova aba ou exibe como preview

### Limpeza de uploads não confirmados

O sincronizador (tarefa 05) executa limpeza diária:
- Busca `anexos` com `upload_confirmado = false` e `criado_em < agora - 1h`
- Para cada um: tenta deletar objeto do S3 (se existir); deleta o registro em `anexos`

### Exclusão de anexo

- Usuário pode excluir qualquer anexo de seu próprio lançamento
- Backend deleta o objeto do S3 e o registro em `anexos`
- Cascata: exclusão do lançamento exclui todos os anexos (FK CASCADE + hook de limpeza S3)

---

## Endpoints

### `POST /lancamentos/{id}/anexos/url-upload`
- Autenticação: obrigatória — somente dono do lançamento
- Body: `nome_original`, `mime_type`, `tamanho_bytes`
- Validações: MIME na whitelist, tamanho ≤ 10 MB, total de anexos do lançamento < 5
- Response 200: `{ "upload_url": str, "anexo_id": UUID, "expira_em": TIMESTAMPTZ }`

### `POST /lancamentos/{id}/anexos/{anexo_id}/confirmar`
- Autenticação: obrigatória — somente dono
- Sem body
- Response 200: anexo confirmado com `mime_type`, `tamanho_bytes`

### `GET /lancamentos/{id}/anexos`
- Autenticação: obrigatória — somente dono
- Response 200: lista de anexos confirmados com `nome_original`, `mime_type`, `tamanho_bytes`,
  `url_thumbnail` (se disponível)

### `GET /lancamentos/{id}/anexos/{anexo_id}/url-download`
- Autenticação: obrigatória — somente dono
- Response 200: `{ "url": str, "expira_em": TIMESTAMPTZ }` (URL válida por 15 minutos)

### `DELETE /lancamentos/{id}/anexos/{anexo_id}`
- Autenticação: obrigatória — somente dono
- Response 200

---

## Configuração de ambiente

Variáveis de ambiente necessárias (backend):

| Variável | Descrição |
|---|---|
| `S3_BUCKET_ANEXOS` | Nome do bucket |
| `AWS_ACCESS_KEY_ID` | Credencial AWS (ou MinIO) |
| `AWS_SECRET_ACCESS_KEY` | Credencial AWS (ou MinIO) |
| `AWS_REGION` | Região (ou endpoint MinIO via `S3_ENDPOINT_URL`) |
| `S3_ENDPOINT_URL` | URL do MinIO em dev (vazio em produção AWS) |

**Desenvolvimento local:** usar MinIO via Docker Compose, adicionando serviço `minio` ao
`compose.yml` existente.

---

## Frontend

### Área de anexos no modal de lançamento (tarefas 07/08)

Seção "Anexos" no modal `ModalCriarDespesaComponent` e `ModalCriarReceitaComponent`,
visível após criar o lançamento (segunda abertura via "editar"):

- Grid de thumbnails (imagens) ou chips de arquivo (PDFs)
- Botão "+ Adicionar anexo" → input `<file>` oculto com `accept` restrito ao whitelist
- Ao selecionar arquivo: executar fluxo 3 etapas (solicitar URL → PUT → confirmar)
- Progress bar durante upload
- Erro amigável se MIME/tamanho inválido

### Visualização no detalhe do lançamento

- Grid 2×2 de thumbnails para imagens
- Clique em thumbnail ou chip de PDF → `GET url-download` → abrir em nova aba
- Ícone de lixeira por item para excluir
- Número de anexos exibido como badge no item de lançamento na tabela (opcional, se houver)

### `AnexosService` (Angular, singleton)

Métodos: `listar(lancamentoId)`, `solicitarUpload(lancamentoId, dados)`,
`fazerUpload(url, arquivo, onProgress)`, `confirmar(lancamentoId, anexoId)`,
`obterUrlDownload(lancamentoId, anexoId)`, `excluir(lancamentoId, anexoId)`

---

## Verificação

```bash
# 1. Solicitar URL de upload
curl -s -X POST http://localhost:8000/lancamentos/$ID/anexos/url-upload \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"nome_original":"nota_fiscal.pdf","mime_type":"application/pdf","tamanho_bytes":204800}' \
  | python3 -m json.tool
# esperado: upload_url (URL S3 assinada), anexo_id

# 2. Upload direto para S3 (simular com curl)
curl -s -X PUT "$UPLOAD_URL" \
  -H "Content-Type: application/pdf" \
  --data-binary @nota_fiscal.pdf
# esperado: 200 sem body (S3 padrão)

# 3. Confirmar upload
curl -s -X POST http://localhost:8000/lancamentos/$ID/anexos/$ANEXO_ID/confirmar \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: upload_confirmado=true, tamanho_bytes preenchido

# 4. Listar anexos do lançamento
curl -s http://localhost:8000/lancamentos/$ID/anexos \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: lista com 1 anexo confirmado

# 5. Obter URL de download
curl -s http://localhost:8000/lancamentos/$ID/anexos/$ANEXO_ID/url-download \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: url assinada GET com expira_em

# 6. Excluir anexo
curl -s -X DELETE http://localhost:8000/lancamentos/$ID/anexos/$ANEXO_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# esperado: 200; GET /anexos retorna lista vazia

# 7. MIME não permitido → 422
# 8. Tamanho > 10MB → 422
# 9. 6º anexo no mesmo lançamento → 422 "Limite de 5 anexos atingido"
```

Frontend:
- Abrir lançamento existente → seção "Anexos" visível
- Adicionar imagem JPEG → thumbnail aparece após confirmação
- Adicionar PDF → chip com nome e ícone de documento
- Clicar no PDF → abre em nova aba
- Excluir anexo → some da lista

---

## Fora do escopo

- Thumbnail gerado para PDFs (somente imagens têm thumbnail)
- Compressão automática de imagens antes do upload
- Annotation de PDF / edição de imagem in-app
- Compartilhamento de anexos com o parceiro
- Quota de armazenamento por usuário
- Suporte a vídeos (tamanho grande, latência de streaming)
- Busca por conteúdo de documento (OCR)
