# Tarefa 27 — Exportação PDF e XLSX

## Contexto

Implementa a geração e download de relatórios financeiros em PDF e extratos em XLSX diretamente
do backend. O usuário pode exportar qualquer relatório (tarefa 12), o extrato de uma conta
(tarefa 15) ou a visão compartilhada do casal (tarefa 13) como arquivo para guardar, enviar
por e-mail ou imprimir.

A geração acontece no servidor — o frontend não monta o documento. O backend retorna o arquivo
binário ou uma URL de download temporária.

**Pré-requisito:** tarefas 01–26 concluídas. Requer tarefas 12 (relatórios), 15 (contas), 13 (casal).

**Dependências novas:**
- `weasyprint==62.3` — geração de PDF a partir de HTML+CSS (Python)
- `openpyxl==3.1.5` — geração de XLSX (já listada na tarefa 07; confirmar presença)

---

## O que pode ser exportado

| Exportação | Formato | Endpoint |
|---|---|---|
| Relatório R1 — Distribuição financeira | PDF + XLSX | `GET /exportar/relatorio/distribuicao` |
| Relatório R2 — Tendência de categorias | PDF + XLSX | `GET /exportar/relatorio/tendencia-categorias` |
| Relatório R3 — Compromissos futuros | PDF | `GET /exportar/relatorio/compromissos` |
| Relatório R4 — Parcelas ativas | PDF + XLSX | `GET /exportar/relatorio/parcelas-ativas` |
| Extrato de conta (tarefa 15) | PDF + XLSX | `GET /exportar/conta/{id}/extrato` |
| Lançamentos do mês | XLSX | `GET /exportar/lancamentos` |
| Visão compartilhada do casal | PDF | `GET /exportar/casal/lancamentos` |
| Fechamento do casal | PDF | `GET /exportar/casal/fechamento/{id}` |

---

## Regras de negócio

### Parâmetros comuns

Todos os endpoints aceitam:
- `formato` (`pdf` ou `xlsx`) — se o formato não for suportado pelo endpoint, retornar 400
- Params de filtro próprios de cada relatório (mes, mes_inicio, mes_fim, etc.) — idênticos
  ao endpoint de dados original

### Autenticação e ownership

- Todos os endpoints exigem autenticação
- Dados exportados filtrados pelo `usuario_id` autenticado (mesmo isolamento dos endpoints de leitura)

### Conteúdo do PDF

Cada PDF inclui:
- Cabeçalho: logo textual "CasalEconomia", nome do usuário, data de geração
- Título do relatório e período consultado
- Tabelas e valores formatados em PT-BR (R$ 1.234,56; datas dd/mm/aaaa)
- Rodapé: "Gerado em [data hora] por CasalEconomia"
- Sem gráficos no PDF (Chart.js não roda no servidor); substituir R2 por tabela de valores

### Conteúdo do XLSX

Cada aba do arquivo:
- Linha 1: título do relatório e período
- Linha 2: vazia (espaçamento)
- Linha 3+: cabeçalho de colunas (negrito, fundo cinza claro)
- Dados a partir da linha 4
- Última linha: totais (negrito) onde aplicável
- Coluna de valores: formatados como número com 2 casas decimais (tipo `NUMBER` do Excel)
- Coluna de datas: tipo `DATE` do Excel (dd/mm/aaaa)
- Largura de colunas ajustada automaticamente ao conteúdo

### Resposta HTTP

- O endpoint retorna o arquivo binário diretamente com:
  - `Content-Type: application/pdf` ou `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `Content-Disposition: attachment; filename="<nome-do-arquivo>"`
  - `Cache-Control: private, no-store`
- Nome do arquivo gerado dinamicamente: `casal-economia-<tipo>-<mes>.<extensão>`
  Exemplo: `casal-economia-distribuicao-2026-11.pdf`

### Tempo de geração

PDFs complexos (muitos lançamentos) podem demorar. Se a geração ultrapassar 10 segundos,
o endpoint retorna 202 com um `job_id` e o arquivo fica disponível em
`GET /exportar/jobs/{job_id}` (polling). Para o MVP: geração síncrona, sem fila;
documentar limite de ~500 lançamentos por exportação como restrição conhecida.

---

## Endpoints

### `GET /exportar/relatorio/distribuicao`
- Query params: `mes_inicio`, `mes_fim`, `escopo`, `formato`
- Response: arquivo PDF ou XLSX

### `GET /exportar/relatorio/tendencia-categorias`
- Query params: `meses` (3/6/12), `formato`
- Response: arquivo PDF (tabela em vez de gráfico) ou XLSX

### `GET /exportar/relatorio/compromissos`
- Query params: `meses_futuros`, `formato=pdf` (somente PDF)
- Response: arquivo PDF

### `GET /exportar/relatorio/parcelas-ativas`
- Query params: `formato`
- Response: arquivo PDF ou XLSX

### `GET /exportar/conta/{id}/extrato`
- Query params: `mes`, `formato`
- Validação: conta pertence ao usuário
- Response: arquivo PDF ou XLSX

### `GET /exportar/lancamentos`
- Query params: `mes`, `tipo` (receita/despesa/todos), `formato=xlsx` (somente XLSX)
- Response: arquivo XLSX

### `GET /exportar/casal/lancamentos`
- Query params: `mes`, `formato=pdf` (somente PDF)
- Requer parceiro conectado (403 se sem parceiro)
- Response: arquivo PDF com lançamentos de ambos

### `GET /exportar/casal/fechamento/{id}`
- Validação: fechamento pertence ao casal do usuário
- Query params: `formato=pdf` (somente PDF)
- Response: arquivo PDF com detalhe do fechamento (quem deve, quanto, lançamentos que compõem)

---

## Novos arquivos backend

| Arquivo | Ação |
|---|---|
| `api/app/services/exportacao.py` | Criar — lógica de geração de PDF e XLSX |
| `api/app/templates/pdf/` | Criar — templates HTML Jinja2 para cada tipo de PDF |
| `api/app/routers/exportacao.py` | Criar — 8 endpoints |
| `api/app/main.py` | Atualizar — incluir router |

Templates HTML usados pelo WeasyPrint ficam em `api/app/templates/pdf/`:
- `base.html` — cabeçalho/rodapé comuns
- `distribuicao.html`, `tendencia.html`, `compromissos.html`, `parcelas.html`
- `extrato_conta.html`, `lancamentos.html`, `casal_lancamentos.html`, `fechamento.html`

---

## Frontend

### Botão de exportação nos relatórios (tarefa 12)

Adicionar botão "Exportar" (ícone `heroArrowDownTray`) no topo de cada aba da tela `/relatorios`:
- Dropdown com opções disponíveis para aquela aba: "PDF" e/ou "XLSX"
- Clique → `GET /exportar/relatorio/<tipo>?...` com os filtros atuais da tela
- O browser recebe o arquivo com `Content-Disposition: attachment` e baixa automaticamente
- Spinner no botão durante o download

### Botão de exportação no extrato de conta (tarefa 15)

Botão "Exportar extrato" no topo da tela `/contas/:id/extrato`:
- Dropdown: "PDF" e "XLSX"
- Mês exportado = mês atualmente selecionado

### Botão de exportação na visão compartilhada (tarefa 13)

- Aba "Lançamentos": botão "Exportar PDF" → visão consolidada de ambos no mês
- Aba "Fechamento": botão "Exportar PDF" em cada fechamento registrado no histórico

### Botão na tela de lançamentos (`/lancamentos`)

Botão "Exportar XLSX" no topo:
- Exporta os lançamentos do mês atual com os filtros aplicados (tipo, busca)

### `ExportacaoService` (Angular, singleton)

Método genérico `exportar(url: string, nomeArquivo: string)`:
- Chama o endpoint via `HttpClient` com `responseType: 'blob'`
- Cria `URL.createObjectURL(blob)`, simula clique em `<a download>`, revoga a URL
- Encapsula o tratamento de erro (toast de "Falha ao exportar" se 500/timeout)

---

## Verificação

```bash
# 1. Exportar distribuição do mês como PDF
curl -s -o distribuicao_nov.pdf \
  "http://localhost:8000/exportar/relatorio/distribuicao?mes_inicio=2026-11&mes_fim=2026-11&formato=pdf" \
  -H "Authorization: Bearer $TOKEN"
# esperado: arquivo PDF gerado; verificar com: file distribuicao_nov.pdf

# 2. Exportar como XLSX
curl -s -o distribuicao_nov.xlsx \
  "http://localhost:8000/exportar/relatorio/distribuicao?mes_inicio=2026-11&mes_fim=2026-11&formato=xlsx" \
  -H "Authorization: Bearer $TOKEN"
# esperado: arquivo XLSX válido; abrir no LibreOffice/Excel

# 3. Extrato de conta como PDF
curl -s -o extrato_nov.pdf \
  "http://localhost:8000/exportar/conta/$CONTA_ID/extrato?mes=2026-11&formato=pdf" \
  -H "Authorization: Bearer $TOKEN"
# esperado: PDF com cabeçalho + tabela de lançamentos + saldo

# 4. Conta de outro usuário → 400

# 5. Formato não suportado para o endpoint
curl -s "http://localhost:8000/exportar/relatorio/compromissos?meses_futuros=3&formato=xlsx" \
  -H "Authorization: Bearer $TOKEN"
# esperado: 400 "Formato xlsx não suportado para este relatório"

# 6. PDF de fechamento do casal
curl -s -o fechamento.pdf \
  "http://localhost:8000/exportar/casal/fechamento/$FECHAMENTO_ID?formato=pdf" \
  -H "Authorization: Bearer $TOKEN"
# esperado: PDF com quem deve, valor, e tabela de lançamentos que compõem o cálculo
```

Frontend:
- Abrir `/relatorios` aba Distribuição → botão "Exportar" → dropdown PDF/XLSX
- Clicar PDF → download automático com nome `casal-economia-distribuicao-2026-11.pdf`
- Abrir o PDF → cabeçalho com nome do usuário, tabela de categorias, rodapé com data
- Extrato de conta → "Exportar XLSX" → planilha com lançamentos do mês, saldos na última linha
- Visão do casal → fechamento registrado → "Exportar PDF" → comprovante do fechamento

---

## Fora do escopo

- Envio automático por e-mail agendado (relatório semanal/mensal)
- Exportação de todos os dados históricos de uma vez (data export — tarefa 19 pode cobrir isso)
- PDF com gráficos renderizados (exige Chromium headless — custo de infra)
- Personalização do layout do PDF pelo usuário
- Assinatura digital do PDF
- Fila de jobs assíncrona para exportações longas (MVP gera de forma síncrona)
