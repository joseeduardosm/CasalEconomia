/**
 * Widget de resumo financeiro do mês com 4 cards clicáveis.
 *
 * pq existe: Angular standalone component com signals.
 * para que no projeto: exibe total de receitas, despesas, saldo e a pagar
 *                      com subvalores; ao clicar emite filtro para o drawer.
 */

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CurrencyPipe } from '@angular/common';

@Component({
  selector: 'app-resumo-mes',
  standalone: true,
  imports: [CurrencyPipe],
  templateUrl: './resumo-mes.component.html',
  styleUrl: './resumo-mes.component.scss',
})
export class ResumoMesComponent {
  @Input({ required: true }) resumo!: any;
  @Input({ required: true }) mes!: string;
  @Output() abrirDrawer = new EventEmitter<any>();

  get nomeMes(): string {
    if (!this.mes) return '';
    const [ano, m] = this.mes.split('-');
    return new Date(+ano, +m - 1).toLocaleDateString('pt-BR', { month: 'long' });
  }

  abrirReceitas(): void {
    this.abrirDrawer.emit({ titulo: `Receitas de ${this.nomeMes}`, mes: this.mes, tipo: 'receita' });
  }

  abrirDespesas(): void {
    this.abrirDrawer.emit({ titulo: `Despesas de ${this.nomeMes}`, mes: this.mes, tipo: 'despesa' });
  }

  abrirSaldo(): void {
    this.abrirDrawer.emit({ titulo: `Lançamentos de ${this.nomeMes}`, mes: this.mes });
  }

  abrirAPagar(): void {
    this.abrirDrawer.emit({ titulo: `A pagar em ${this.nomeMes}`, mes: this.mes, tipo: 'despesa', liquidado: false });
  }
}
