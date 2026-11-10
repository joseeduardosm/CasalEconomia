/**
 * Tela do painel principal do CasalEconomia.
 * Destino após login — exibe resumo financeiro do mês ativo.
 * Implementação completa prevista em tarefa futura.
 *
 * pq existe: Angular standalone component — unidade de UI autossuficiente
 *            que declara suas próprias dependências sem NgModule.
 * para que no projeto: primeira tela após autenticação; ponto de entrada
 *                      do AppShell e vitrine do resumo financeiro mensal.
 */

import { Component } from '@angular/core';

@Component({
  selector: 'app-painel',
  standalone: true,
  template: `
    <div class="pagina-placeholder">
      <h1>Painel</h1>
      <p>Em construção — resumo financeiro chegará em breve.</p>
    </div>
  `,
  styles: [`
    .pagina-placeholder { padding: 24px; }
    h1 { font-family: var(--font-heading); font-size: 24px; font-weight: 400; margin-bottom: 8px; }
    p { color: var(--color-warm-gray); font-size: 14px; }
  `],
})
export class PainelComponent {}
