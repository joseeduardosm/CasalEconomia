# T28 — Rascunho automático de formulários

## Objetivo
Salvar automaticamente o estado de preenchimento dos modais de criação/edição de lançamentos no
navegador, restaurando-o na próxima abertura com um aviso visível e a opção de descartar.

---

## Contexto e motivação
O usuário começa a preencher uma despesa, fecha o modal por acidente (ou recarrega a página) e
perde tudo. Com rascunho automático, os dados são recuperados na reabertura sem nenhuma ação
deliberada do usuário — basta reabrir o modal.

---

## Comportamento esperado

### Salvamento
- A cada alteração em qualquer campo do modal, o estado completo do formulário é persistido no
  `localStorage` do navegador sob uma chave específica por modal.
- O salvamento inclui data e hora exatos no momento do último save.
- Dados salvos: todos os campos preenchíveis (descrição, valor, data, forma de pagamento,
  categoria, conta/cartão, nota, parcelamento, parceiro, recorrência).
- Anexos **não** são salvos no rascunho (são arquivos binários; isso é comunicado no aviso).

### Restauração
- Ao abrir o modal, se existir rascunho salvo, os campos são preenchidos com os valores do rascunho.
- Um aviso aparece no topo do formulário:
  > _"Rascunho restaurado (salvo em 08/11/2026 às 14:32). Os anexos não são guardados no rascunho."_
  - Botão **Descartar rascunho**: limpa o localStorage e reinicializa o formulário vazio.

### Limpeza
- Ao submeter o formulário com sucesso (criação ou edição), o rascunho é apagado automaticamente.
- Ao fechar o modal sem salvar, o rascunho **permanece** (proteção contra fechamento acidental).
- Rascunhos com mais de 7 dias são ignorados na restauração e descartados silenciosamente.

---

## Modais que ganham rascunho

| Modal                          | Chave localStorage                    |
| ------------------------------ | ------------------------------------- |
| Criar despesa                  | `rascunho_despesa`                    |
| Editar despesa                 | `rascunho_despesa_<id>`               |
| Criar receita                  | `rascunho_receita`                    |
| Editar receita                 | `rascunho_receita_<id>`               |

---

## Sem mudança de backend
Esta funcionalidade é 100% frontend. Nenhum endpoint novo é necessário.

---

## Regras de negócio

1. O salvamento é local ao navegador — ao usar outro dispositivo/navegador, não há rascunho.
2. O aviso de restauração só aparece se o rascunho tiver pelo menos um campo preenchido (evitar
   aviso com rascunho vazio).
3. Se o modal for aberto para editar um lançamento já existente (pré-preenchido pela API), o
   rascunho salvo tem prioridade se for mais recente que a abertura anterior do mesmo registro.
4. Nunca salvar senhas, tokens ou hashes no rascunho.

---

## Telas impactadas

| Tela                          | Impacto                                              |
| ----------------------------- | ---------------------------------------------------- |
| `/lancamentos`                | Modais de criar/editar despesa e receita             |
| `/painel`                     | Modais abertos pelo atalho rápido do painel          |
| `/extrato/:contaId`           | Modal de edição aberto pelo extrato de conta         |

---

## Verificação

```
# Nenhum endpoint para testar — verificação manual:
# 1. Abrir modal de nova despesa → preencher descrição "Teste rascunho" e valor "150"
# 2. Fechar modal sem salvar (X ou Esc)
# 3. Reabrir modal de nova despesa
# → Campos recuperados + aviso de rascunho com data e hora exatos
# → Clicar "Descartar rascunho" → formulário limpo, aviso some
# 4. Preencher e salvar com sucesso → reabrir modal → formulário vazio (rascunho foi limpo)
```

---

## Fora de escopo

- Sincronização de rascunho entre dispositivos (seria via API — não está no escopo desta tarefa).
- Rascunho de formulários que não são de lançamento (ex.: formulários de meta, conta, cartão).
- Versioning de rascunho (histórico de saves anteriores).
