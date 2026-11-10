# Tarefa 21 — Importação de Extrato Bancário (OFX)

## Contexto

Permite importar extratos bancários no formato OFX (Open Financial Exchange), padrão exportado
pela maioria dos bancos brasileiros (Nubank, Inter, Itaú, Bradesco, Caixa, etc.). O usuário
baixa o extrato do internet banking e faz o upload no sistema; o backend analisa o arquivo,
detecta duplicatas e apresenta uma pré-visualização para confirmação antes de criar os lançamentos.

O fluxo é de **dois passos** (igual à importação XLSX da tarefa 07): validar/analisar → confirmar.
Sem criação automática silenciosa — o usuário sempre revisa antes de confirmar.

**Pré-requisito:** tarefas 01–20 concluídas. Requer tarefas 07/08 (lancamentos) e 15 (contas).

**Dependência nova:** `ofxparse==0.21` (biblioteca Python para parsear OFX).

---

## Conceito de duplicata

Dois lançamentos são considerados duplicata quando:
- `data_lancamento` igual E
- `valor` igual (módulo) E
- `descricao` similar (≥ 80% via distância Levenshtein ou match exato do campo MEMO do OFX) OU
- `externalId` igual (campo `FITID` do OFX — identificador único da transação no banco)

O campo `external_id` é adicionado em `lancamentos` para armazenar o `FITID` do OFX.

---

## Nova coluna em `lancamentos`

| Campo | Tipo | Notas |
|---|---|---|
| `external_id` | VARCHAR(100) | FITID do OFX; índice único (usuario_id + external_id) para evitar duplicata |

---

## Formato OFX

O arquivo OFX (versão 1.x ou 2.x) contém uma lista de `STMTTRN` (transações) com campos:

| Campo OFX | Campo em lancamentos |
|---|---|
| `TRNTYPE` (DEBIT/CREDIT) | `tipo` (despesa/receita) |
| `DTPOSTED` | `data_lancamento` |
| `TRNAMT` | `valor` (absoluto; sinal define tipo) |
| `FITID` | `external_id` |
| `MEMO` ou `NAME` | `descricao` |

---

## Regras de negócio

### Validação do arquivo

- Aceitar apenas arquivos `.ofx` ou `.qfx` (MIME `application/x-ofx` ou texto)
- Tamanho máximo: 5 MB
- Rejeitar se não parsear como OFX válido: 422 com descrição do erro
- Rejeitar se não contiver transações (`STMTTRN`): 422

### Análise de duplicatas (passo 1 — `/lancamentos/importar-ofx`)

Para cada transação do OFX:
1. Verificar se já existe em `lancamentos` com mesmo `external_id` e mesmo `usuario_id` →
   marcar como `duplicata_exata: true`
2. Verificar se já existe lançamento com mesma data, valor e descrição similar →
   marcar como `duplicata_provavel: true`
3. Retornar todas as transações com `status_importacao`:
   - `novo` — não encontrado no banco; será criado ao confirmar
   - `duplicata_exata` — FITID já existe; não será criado
   - `duplicata_provavel` — possível duplicata; usuário pode forçar importação individualmente

### Confirmação (passo 2 — `/lancamentos/importar-ofx/confirmar`)

Body: lista de `external_id` selecionados pelo usuário para importar (apenas os `novo` e os
`duplicata_provavel` que o usuário optou por importar mesmo assim).

Para cada item confirmado:
- Criar lançamento com `conta_id` (fornecido pelo usuário no passo 1), `liquidado = true`,
  `external_id`, `categoria_id = null` (usuário categoriza depois), `forma_pagamento = "outro"`
- Retornar contagem de criados e lista de IDs

### Mapeamento de tipo

- `TRNAMT > 0` → `tipo = receita`
- `TRNAMT < 0` → `tipo = despesa`, `valor = abs(TRNAMT)`

---

## Endpoints

### `POST /lancamentos/importar-ofx`
- Autenticação: obrigatória
- Multipart form: campo `arquivo` (OFX), campo `conta_id` (UUID da conta destino)
- Validações: arquivo válido, conta pertence ao usuário
- Response 200:
  ```
  {
    "total": int,
    "novos": int,
    "duplicatas_exatas": int,
    "duplicatas_provaveis": int,
    "transacoes": [
      {
        "external_id": str,
        "descricao": str,
        "data": DATE,
        "valor": NUMERIC,
        "tipo": "receita" | "despesa",
        "status_importacao": "novo" | "duplicata_exata" | "duplicata_provavel",
        "lancamento_existente_id": UUID | null
      }
    ]
  }
  ```

### `POST /lancamentos/importar-ofx/confirmar`
- Autenticação: obrigatória
- Body: `conta_id` (UUID), `external_ids: [str]` — IDs a importar
- Response 201: `{ "criados": int, "ids": [UUID] }`

---

## Frontend

### Entrada no fluxo de importação

Adicionar opção "Importar extrato OFX" no menu de importação (junto com "Importar XLSX" da
tarefa 07). Ambos ficam em um botão com dropdown de opção de importação.

### `ImportacaoOfxComponent` (modal de dois passos)

**Passo 1 — Upload:**
- Select de conta de destino (`conta_id`)
- Drop zone ou input de arquivo para `.ofx` / `.qfx`
- Instrução: "Baixe o extrato do seu banco em formato OFX e faça o upload aqui"
- Botão "Analisar arquivo"
- Exibir spinner e mensagem "Analisando..."

**Passo 2 — Pré-visualização:**
- Resumo: "X transações encontradas — Y novas, Z duplicatas"
- `TabelaLancamentosComponent` com colunas: Selecionar (checkbox), Descrição, Data, Valor,
  Tipo, Status
- Linhas com `status_importacao = "duplicata_exata"`: desabilitadas, riscadas, tooltip explicando
- Linhas com `status_importacao = "duplicata_provavel"`: desmarcadas por padrão com aviso amarelo;
  usuário pode marcar manualmente para incluir
- Linhas com `status_importacao = "novo"`: marcadas por padrão
- Checkbox "Selecionar todos os novos"
- Botão "Importar selecionados (X)" → `POST /lancamentos/importar-ofx/confirmar`

**Pós-importação:**
- Toast: "X lançamentos importados com sucesso"
- Fechar modal → `/lancamentos` atualizado

### `ImportacaoService` (Angular, singleton)

Métodos (compartilhados com importação XLSX da T07): `analisarOfx(arquivo, contaId)`,
`confirmarOfx(contaId, externalIds)`, `analisarXlsx(arquivo)`, `confirmarXlsx(dados)`

---

## Verificação

```bash
# 1. Upload de arquivo OFX válido
curl -s -X POST http://localhost:8000/lancamentos/importar-ofx \
  -H "Authorization: Bearer $TOKEN" \
  -F "arquivo=@extrato_novembro.ofx" \
  -F "conta_id=<uuid>" \
  | python3 -m json.tool
# esperado: lista de transacoes com status_importacao

# 2. Confirmar apenas os novos
curl -s -X POST http://localhost:8000/lancamentos/importar-ofx/confirmar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"conta_id":"<uuid>","external_ids":["FITID001","FITID002"]}' \
  | python3 -m json.tool
# esperado: criados=2, ids=[...]

# 3. Segunda importação do mesmo arquivo → todos marcados como duplicata_exata
curl -s -X POST http://localhost:8000/lancamentos/importar-ofx \
  -H "Authorization: Bearer $TOKEN" -F "arquivo=@extrato_novembro.ofx" -F "conta_id=<uuid>" \
  | python3 -m json.tool
# esperado: duplicatas_exatas = total do arquivo; novos = 0

# 4. Arquivo inválido → 422 com mensagem de erro

# 5. Conta de outro usuário → 400
```

Frontend:
- Abrir importação OFX → fazer upload de arquivo → ver pré-visualização com status das transações
- Duplicatas desabilitadas → botão importa apenas os novos
- Após confirmar → lançamentos aparecem em `/lancamentos` vinculados à conta selecionada

---

## Fora do escopo

- Importação automática (scraping ou open banking)
- Importação de múltiplas contas no mesmo arquivo
- Regras de categorização automática por MEMO (ML)
- Suporte a formato CNAB (padrão legado de alguns bancos)
- Mapeamento de transferências detectadas no OFX para o módulo de transferências (tarefa 18)
- Edição de campos (descrição, categoria) durante a pré-visualização de importação
