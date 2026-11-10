/**
 * Tela de lançamentos do CasalEconomia.
 * Placeholder — implementação completa prevista em tarefa futura.
 *
 * pq existe: Angular standalone component com carregamento tardio (lazy) —
 *            o código só é baixado quando o usuário acessa a rota.
 * para que no projeto: módulo de registro de receitas e despesas do casal;
 *                      consumirá o período ativo do PeriodoService.
 */

import { Component } from '@angular/core';

@Component({
  selector: 'app-lancamentos',
  standalone: true,
  template: `
    <div class="pagina-placeholder">
      <h1>Lançamentos</h1>
      <p>Em construção.</p>
    </div>
  `,
  styles: [`
    .pagina-placeholder { padding: 24px; }
    h1 { font-family: var(--font-heading); font-size: 24px; font-weight: 400; margin-bottom: 8px; }
    p { color: var(--color-warm-gray); font-size: 14px; }
  `],
})
export class LancamentosComponent {}
