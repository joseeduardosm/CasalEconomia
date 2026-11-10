/**
 * Widget de faturas de cartão abertas no mês.
 *
 * pq existe: Angular standalone component com signals.
 * para que no projeto: lista faturas com destaque para vencimentos próximos,
 *                      emite filtro para o drawer ao clicar.
 */

import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-faturas-card',
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './faturas-card.component.html',
  styleUrl: './faturas-card.component.scss',
})
export class FaturasCardComponent {
  @Input({ required: true }) faturas!: any[];
  @Input({ required: true }) mes!: string;
  @Output() abrirDrawer = new EventEmitter<any>();

  private router = inject(Router);

  abrirFatura(f: any): void {
    this.abrirDrawer.emit({
      titulo: `Lançamentos — ${f.cartao_nome} ${this.mes}`,
      mes: this.mes,
      cartao_id: f.cartao_id,
    });
  }

  verFaturaCompleta(f: any, event: Event): void {
    event.stopPropagation();
    this.router.navigate(['/cartoes', f.cartao_id, 'fatura']);
  }
}
