/**
 * Widget de próximos vencimentos e itens vencidos não pagos.
 *
 * pq existe: Angular standalone component com signals.
 * para que no projeto: destaca visualmente vencimentos urgentes
 *                      e emite evento para o drawer ao clicar.
 */

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CurrencyPipe } from '@angular/common';

@Component({
  selector: 'app-proximos-vencimentos',
  standalone: true,
  imports: [CurrencyPipe],
  templateUrl: './proximos-vencimentos.component.html',
  styleUrl: './proximos-vencimentos.component.scss',
})
export class ProximosVencimentosComponent {
  @Input({ required: true }) vencimentos!: any[];
  @Output() abrirDrawer = new EventEmitter<any>();

  abrirDetalhe(item: any): void {
    this.abrirDrawer.emit({ titulo: 'Detalhe do lançamento', lancamento: item });
  }

  labelVencimento(item: any): string {
    if (item.vencido) return 'Vencido';
    if (item.dias_para_vencer === 0) return 'Vence hoje';
    if (item.dias_para_vencer === 1) return 'Vence amanhã';
    return `Vence em ${item.dias_para_vencer} dias`;
  }
}
