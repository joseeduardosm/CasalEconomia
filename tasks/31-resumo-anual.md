# T31 — Resumo anual do casal

## Objetivo
Oferecer uma visão consolidada do ano financeiro do casal: totais de receitas e despesas por mês,
categorias que mais pesaram, evolução do saldo, metas alcançadas e principais métricas — tudo em
uma única tela de leitura pensada para uma revisão rápida do ano inteiro.

---

## Contexto e motivação
O painel (`/painel`) foca no mês corrente. O resumo anual responde a perguntas como: _"Em qual mês
gastamos mais este ano? Quanto viajamos no total? Conseguimos economizar mais do que no ano
passado?"_ — sem ter que navegar mês a mês manualmente.

---

## Rota
`/resumo-anual` — seletor de ano no topo (padrão: ano atual).

---

## Seções da tela

### 1. Cabeçalho — métricas do ano

| Métrica                        | Descrição                                              |
| ------------------------------ | ------------------------------------------------------ |
| Total de receitas               | Soma de todos os lançamentos de receita do ano         |
| Total de despesas               | Soma de todas as despesas do ano                       |
| Resultado (saldo do ano)        | Receitas − Despesas                                    |
| Maior despesa única             | Lançamento de maior valor no ano (com link direto)     |
| Mês mais caro                   | Mês com maior total de despesas                        |
| Mês mais lucrativo              | Mês com maior saldo positivo                           |

### 2. Gráfico de barras mensais
- Eixo X: Jan a Dez.
- Barras: receitas (verde) e despesas (vermelho) lado a lado por mês.
- Clicável: ao clicar no mês, navega para `/lancamentos?mes=YYYY-MM`.

### 3. Top 5 categorias de despesas
- Tabela: categoria, total gasto, percentual do total anual de despesas.
- Ícone e cor da categoria.

### 4. Evolução mensal acumulada
- Linha do saldo acumulado ao longo do ano (Jan → Dez), mostrando se o casal está ganhando ou
  perdendo ao longo dos meses.

### 5. Metas do ano
- Lista de metas com prazo no ano selecionado.
- Para cada meta: nome, valor-alvo, valor alcançado, percentual e status (atingida / em andamento /
  não alcançada).

### 6. Comparativo com ano anterior
- Bloco de comparação: receitas, despesas e resultado do ano atual vs. ano anterior.
- Variação em % com seta verde (melhorou) ou vermelha (piorou).

---

## Endpoint

### `GET /relatorios/resumo-anual?ano=2026`

**Resposta:**
```json
{
  "data": {
    "ano": 2026,
    "total_receitas": 85000.00,
    "total_despesas": 72000.00,
    "resultado": 13000.00,
    "maior_despesa": { "id": "...", "descricao": "Passagem Europa", "valor": 8500.00 },
    "mes_mais_caro": { "mes": "07", "total": 9200.00 },
    "mes_mais_lucrativo": { "mes": "12", "saldo": 3100.00 },
    "por_mes": [
      { "mes": "01", "receitas": 7000.00, "despesas": 5800.00 },
      ...
    ],
    "top_categorias": [
      { "categoria_nome": "Moradia", "total": 18000.00, "percentual": 25.0 },
      ...
    ],
    "metas": [
      { "id": "...", "nome": "Viagem Europa", "alvo": 10000.00, "alcancado": 8500.00, "status": "nao_alcancada" },
      ...
    ],
    "comparativo_ano_anterior": {
      "receitas_anterior": 78000.00,
      "despesas_anterior": 71000.00,
      "resultado_anterior": 7000.00
    }
  }
}
```

---

## Regras de negócio

1. Apenas lançamentos marcados como pagos (`pago = true`) entram nos totais.
2. Transferências entre contas são excluídas dos totais (já tratado na T18).
3. Lançamentos do parceiro compartilhados e aceitos são incluídos.
4. Se o ano selecionado for o corrente, os meses futuros aparecem com valor zero mas são
   exibidos (perspectiva do ano inteiro).
5. O comparativo com o ano anterior só aparece se houver dados do ano anterior.
6. `maior_despesa` considera apenas despesas pessoais (não compartilhadas pelo parceiro).

---

## Verificação

```
# Resumo do ano corrente
curl -s "http://localhost:8000/api/relatorios/resumo-anual?ano=2026" \
  -H "Cookie: session=..." | jq '.data.resultado'
# → diferença entre receitas e despesas do ano

# Verificar que transferências não entram no total
# (criar transferência T18, conferir que total_despesas não muda)

# Verificar ano anterior sem dados
curl -s "http://localhost:8000/api/relatorios/resumo-anual?ano=2015" \
  -H "Cookie: session=..." | jq '.data.total_receitas'
# → 0
```

---

## Fora de escopo

- Exportação do resumo em PDF (coberto pela T27 — adicionar tipo "resumo-anual" lá).
- Comparativo de mais de 2 anos simultaneamente.
- Breakdown por pessoa do casal (cada um contribuiu com quanto).
- Projeção de fechamento do ano com base nos meses anteriores.
