# T34 — Patrimônio do casal

## Objetivo
Registrar e acompanhar os bens patrimoniais do casal (imóveis, veículos, eletrodomésticos,
investimentos físicos, etc.) com valor de aquisição, valor atual estimado e depreciação — dando
uma visão completa da situação financeira além do fluxo de caixa mensal.

---

## Contexto e motivação
O app hoje gerencia receitas, despesas e metas, mas não registra o que o casal **possui**. Um
carro, um imóvel ou um fundo de renda fixa são parte do patrimônio e influenciam as decisões
financeiras. Esta tela fecha a visão de riqueza do casal (ativos − passivos = patrimônio líquido).

---

## Nova tabela: `bens`

| Coluna              | Tipo        | Descrição                                               |
| ------------------- | ----------- | ------------------------------------------------------- |
| `id`                | UUID PK     |                                                         |
| `usuario_id`        | FK          | Dono do registro                                        |
| `nome`              | texto       | Ex.: "Apartamento Centro", "Honda Civic 2022"           |
| `categoria`         | texto       | Ver tabela de categorias abaixo                         |
| `valor_aquisicao`   | decimal     | Valor pago na compra/investimento inicial               |
| `data_aquisicao`    | date        |                                                         |
| `valor_atual`       | decimal     | Estimativa do valor atual (atualizado pelo usuário)     |
| `valor_atual_em`    | date        | Data da última atualização do valor atual               |
| `financiado`        | boolean     | Se o bem ainda tem saldo devedor                        |
| `saldo_devedor`     | decimal nullable | Saldo devedor atual (preenchido se `financiado`)   |
| `conta_vinculada_id`| FK nullable | Conta onde as parcelas são debitadas (se financiado)    |
| `nota`              | texto       |                                                         |
| `ativo`             | boolean     | `false` = vendido/baixado (sem excluir histórico)       |
| `criado_em`         | timestamptz |                                                         |
| `atualizado_em`     | timestamptz |                                                         |

### Categorias de bens

| Valor         | Rótulo              |
| ------------- | ------------------- |
| `imovel`      | Imóvel              |
| `veiculo`     | Veículo             |
| `eletronico`  | Eletrônico          |
| `eletrodomestico` | Eletrodoméstico |
| `investimento`| Investimento físico |
| `joia`        | Joias/Relógios      |
| `arte`        | Arte/Colecionáveis  |
| `outro`       | Outros              |

---

## Visão patrimonial: métricas calculadas

| Métrica                        | Cálculo                                                |
| ------------------------------ | ------------------------------------------------------ |
| Patrimônio bruto               | Soma de todos os `valor_atual` dos bens ativos         |
| Total de dívidas               | Soma dos `saldo_devedor` dos bens financiados          |
| Patrimônio líquido             | Patrimônio bruto − Total de dívidas                    |
| Variação desde a aquisição     | `(valor_atual − valor_aquisicao) / valor_aquisicao` %  |

---

## Endpoints

| Método | Rota                        | Ação                                            |
| ------ | --------------------------- | ----------------------------------------------- |
| GET    | `/bens`                     | Lista todos os bens ativos do usuário           |
| POST   | `/bens`                     | Cria novo bem                                   |
| GET    | `/bens/{id}`                | Detalhe do bem                                  |
| PUT    | `/bens/{id}`                | Edita bem                                       |
| PATCH  | `/bens/{id}/valor-atual`    | Atualiza apenas o valor atual estimado          |
| PATCH  | `/bens/{id}/baixar`         | Marca como vendido/baixado (`ativo = false`)    |
| DELETE | `/bens/{id}`                | Remove permanentemente (somente se nunca foi exibido em resumo anual) |
| GET    | `/bens/resumo`              | Totais patrimoniais (bruto, dívidas, líquido)   |

---

## UI — Tela `/patrimonio`

### Cabeçalho
- 3 cards: **Patrimônio bruto**, **Total de dívidas**, **Patrimônio líquido**.

### Lista de bens
- Agrupada por categoria.
- Cada bem: nome, valor atual, data de atualização, badge "Financiado" se aplicável.
- Ícone de edição (drawer lateral) e ação de baixa.

### Drawer de cadastro/edição
- Formulário com todos os campos da tabela.
- Ao marcar `financiado = true`, campos `saldo_devedor` e `conta_vinculada_id` aparecem.
- Botão **"Atualizar valor"**: abre mini-modal só para atualizar `valor_atual` e `valor_atual_em`
  sem abrir o drawer completo.

### Bem baixado (vendido)
- Continua visível em listagem separada "Bens baixados" para histórico.
- Não entra no cálculo de patrimônio bruto.

---

## Regras de negócio

1. `valor_atual` é sempre informado pelo usuário; o sistema não busca cotações externas.
2. `saldo_devedor` é informado pelo usuário; o sistema não calcula amortização.
3. Um bem financiado pode ter `conta_vinculada_id` para facilitar a identificação das despesas
   mensais relacionadas (apenas referência visual — não cria lançamentos automaticamente).
4. `ativo = false` não exclui o bem; ele some do cálculo patrimonial mas fica no histórico.
5. Todo registro filtra por `usuario_id` (o patrimônio do parceiro não é visível por padrão).
6. No MVP, bens não são compartilhados entre parceiros (cada um registra o seu).

---

## Integração com resumo anual (T31)

- O resumo anual pode incluir uma seção adicional "Patrimônio líquido no fechamento do ano"
  — apenas se o usuário tiver pelo menos um bem cadastrado.

---

## Verificação

```
# Criar bem
curl -s -X POST http://localhost:8000/api/bens \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"nome":"Honda Civic","categoria":"veiculo","valor_aquisicao":85000,"data_aquisicao":"2022-03-15","valor_atual":72000,"valor_atual_em":"2026-11-01","financiado":true,"saldo_devedor":35000}' \
  | jq '.data.id'

# Resumo patrimonial
curl -s http://localhost:8000/api/bens/resumo \
  -H "Cookie: session=..." | jq '.data'
# → { "patrimonio_bruto": 72000, "total_dividas": 35000, "patrimonio_liquido": 37000 }

# Atualizar valor atual
curl -s -X PATCH http://localhost:8000/api/bens/<id>/valor-atual \
  -H "Content-Type: application/json" -H "Cookie: session=..." \
  -d '{"valor_atual":70000,"valor_atual_em":"2026-11-08"}' | jq '.data.valor_atual'
# → 70000

# Baixar bem (venda)
curl -s -X PATCH http://localhost:8000/api/bens/<id>/baixar \
  -H "Cookie: session=..."

# Verificar que patrimônio bruto diminuiu
curl -s http://localhost:8000/api/bens/resumo \
  -H "Cookie: session=..." | jq '.data.patrimonio_bruto'
# → 0 (se era o único bem)
```

---

## Fora de escopo

- Cotação automática de ativos (imóvel por IPCA, veículo por tabela FIPE, investimentos por B3).
- Inventário patrimonial compartilhado entre parceiros.
- Relatório de evolução patrimonial ao longo do tempo.
- Integração com corretoras ou Open Finance.
- Cálculo de amortização de financiamento.
