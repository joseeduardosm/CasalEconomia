/**
 * Widget de últimos lançamentos do mês.
 *
 * pq existe: Angular standalone component com signals.
 * para que no projeto: lista os 8 lançamentos mais recentes com ícone
 *                      de tipo, valor colorido e link para ver todos.
 */

import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-lancamentos-recentes',
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './lancamentos-recentes.component.html',
  styleUrl: './lancamentos-recentes.component.scss',
})
export class LancamentosRecentesComponent {
  @Input({ required: true }) lancamentos!: any[];
  @Input({ required: true }) mes!: string;
  @Output() abrirDrawer = new EventEmitter<any>();

  private router = inject(Router);

  abrirDetalhe(item: any): void {
    this.abrirDrawer.emit({ titulo: 'Detalhe do lançamento', lancamento: item });
  }

  verTodos(): void {
    this.router.navigate(['/lancamentos'], { queryParams: { mes: this.mes } });
  }
}
