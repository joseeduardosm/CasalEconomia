/**
 * Widget de visão do parceiro: pendentes para aceitar e resumo bilateral.
 *
 * pq existe: Angular standalone component com signals.
 * para que no projeto: exibe lançamentos pendentes do parceiro com ações
 *                      inline de aceitar/ignorar e resumo lado-a-lado.
 */

import { Component, Input, Output, EventEmitter, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { PainelService } from '../../../core/services/painel.service';

@Component({
  selector: 'app-widget-parceiro',
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './widget-parceiro.component.html',
  styleUrl: './widget-parceiro.component.scss',
})
export class WidgetParceiroComponent {
  @Input({ required: true }) parceiro!: any;
  @Input({ required: true }) mes!: string;
  @Output() atualizar = new EventEmitter<void>();
  @Output() abrirDrawer = new EventEmitter<any>();

  private svc = inject(PainelService);
  private router = inject(Router);

  aceitando = signal<string | null>(null);
  ignorando = signal<string | null>(null);

  aceitar(pendente: any): void {
    this.aceitando.set(pendente.id);
    this.svc.aceitarPendente(pendente.id, pendente.versao_fonte).subscribe({
      next: () => { this.aceitando.set(null); this.atualizar.emit(); },
      error: () => this.aceitando.set(null),
    });
  }

  ignorar(pendente: any): void {
    this.ignorando.set(pendente.id);
    this.svc.ignorarPendente(pendente.id, pendente.versao_fonte).subscribe({
      next: () => { this.ignorando.set(null); this.atualizar.emit(); },
      error: () => this.ignorando.set(null),
    });
  }

  verTodosOsPendentes(): void {
    this.router.navigate(['/lancamentos-parceiro']);
  }

  get porcentagemMinha(): number {
    const total = +this.parceiro.resumo_despesas + +this.minhaDespesaEstimada;
    if (total === 0) return 50;
    return Math.round((+this.minhaDespesaEstimada / total) * 100);
  }

  get minhaDespesaEstimada(): number {
    return 0;
  }
}
