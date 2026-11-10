# T32 — Backup e portabilidade de dados

## Objetivo
Permitir que o usuário exporte todos os seus dados financeiros em um arquivo estruturado (JSON e
CSV), garantindo portabilidade e autonomia sobre seus próprios dados.

---

## Contexto e motivação
O usuário deve poder levar seus dados consigo. Seja para auditoria pessoal, migração de
plataforma ou simplesmente ter uma cópia de segurança local, o export completo é um requisito de
confiança e conformidade com a LGPD (direito à portabilidade).

---

## Dados exportados

| Entidade            | Incluído                                                   |
| ------------------- | ---------------------------------------------------------- |
| Lançamentos         | Todos os campos, incluindo histórico de edições (T29)      |
| Contas bancárias    | Nome, banco, saldo inicial, tipo                           |
| Cartões de crédito  | Nome, bandeira, limite, dia de fechamento/vencimento       |
| Categorias          | Apenas as categorias criadas pelo usuário (não as padrão)  |
| Metas financeiras   | Nome, valor-alvo, prazo, aportes                           |
| Orçamentos          | Categoria, valor mensal configurado                        |
| Recorrências        | Todas as regras de recorrência ativas e pausadas           |
| Transferências      | Todos os registros                                         |
| Reembolsos          | Registros de reembolso e entradas de pagamento             |

**Não exportados:** dados do parceiro (pertence a outra conta), tokens de sessão, dados internos
de autenticação, histórico de notificações.

---

## Formatos disponíveis

### JSON (exportação completa)
- Arquivo único `casal-economia-backup-YYYY-MM-DD.json`.
- Estrutura: um objeto com uma chave por entidade, cada uma com array de registros.
- Inclui metadados: data da exportação, versão do sistema, `usuario_id` (anonimizado como hash).

### CSV (exportação de lançamentos)
- Arquivo `casal-economia-lancamentos-YYYY-MM-DD.csv`.
- Colunas: data, descrição, valor, tipo, forma_pagamento, categoria, conta, cartão, pago, nota.
- Separador: vírgula; encoding: UTF-8 com BOM (compatibilidade com Excel).

---

## Endpoint

### `POST /configuracoes/exportar-dados`

**Body:**
```json
{ "formato": "json" }
```
ou
```json
{ "formato": "csv" }
```

**Resposta:** download direto do arquivo com headers:
- `Content-Disposition: attachment; filename="casal-economia-backup-2026-11-08.json"`
- `Content-Type: application/json` ou `text/csv`
- `Cache-Control: private, no-store`

---

## UI — Configurações → Dados e privacidade

Nova seção na tela de Configurações (`/configuracoes`):

### Exportar meus dados
- Botão **"Baixar backup JSON"** — dispara download do JSON completo.
- Botão **"Exportar lançamentos CSV"** — dispara download do CSV de lançamentos.
- Texto informativo: _"O backup inclui todos os seus lançamentos, contas, cartões, metas e
  configurações. Os dados do seu parceiro não são incluídos."_

### Excluir minha conta
- Botão **"Excluir minha conta"** com confirmação por digitação de texto.
- Aviso: _"Todos os seus dados serão excluídos permanentemente. Lançamentos compartilhados com seu
  parceiro serão removidos da visão dele também."_
- Fluxo de exclusão: digitar "EXCLUIR" → confirmação por e-mail → exclusão imediata.

---

## Regras de negócio

1. A exportação só inclui dados do usuário autenticado; dados do parceiro nunca saem.
2. Lançamentos compartilhados aceitos pelo usuário **são** incluídos no backup (pois estão na sua
   visão financeira).
3. O JSON exportado não contém senhas, tokens, hashes de senha, chaves de API ou dados do sistema.
4. Geração síncrona no MVP — para contas com muitos registros, timeout configurado em 60 s.
5. Rate limit: 1 exportação por formato a cada 10 minutos por usuário.
6. A exclusão de conta gera um e-mail de confirmação para o endereço cadastrado antes de executar
   a exclusão.
7. Ao excluir a conta, o vínculo do casal é desfeito automaticamente.

---

## Verificação

```
# Exportar JSON
curl -s -X POST http://localhost:8000/api/configuracoes/exportar-dados \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"formato": "json"}' \
  -o /tmp/backup.json -w "%{http_code}"
# → 200, arquivo salvo em /tmp/backup.json

# Verificar conteúdo mínimo do JSON
cat /tmp/backup.json | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(list(d.keys()))
"
# → ['lancamentos', 'contas', 'cartoes', 'categorias', 'metas', 'orcamentos', ...]

# Exportar CSV
curl -s -X POST http://localhost:8000/api/configuracoes/exportar-dados \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"formato": "csv"}' \
  -o /tmp/lancamentos.csv -w "%{http_code}"
# → 200, arquivo com cabeçalho CSV

# Verificar rate limit
# (segunda requisição em < 10 min)
curl -s -X POST http://localhost:8000/api/configuracoes/exportar-dados \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"formato": "json"}' | jq '.error'
# → "Aguarde 10 minutos para realizar uma nova exportação"
```

---

## Fora de escopo

- Importação de backup JSON de volta ao sistema.
- Backup automático agendado por e-mail.
- Exportação de dados do casal (ambos os parceiros) em um único arquivo.
- Criptografia do arquivo de backup.
- Integração com Google Drive ou Dropbox.
