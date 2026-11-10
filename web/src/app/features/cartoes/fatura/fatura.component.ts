/**
 * Tela de detalhe de fatura do cartão de crédito.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: exibe o extrato da fatura com lançamentos, valores
 *                      e permite registrar pagamento parcial ou total.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CartaoService } from '../../../core/services/cartao.service';

@Component({
  selector: 'app-fatura',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, RouterLink, FormsModule],
  templateUrl: './fatura.component.html',
  styleUrl: './fatura.component.scss',
})
export class FaturaComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private svc = inject(CartaoService);

  fatura = signal<any>(null);
  carregando = signal(true);
  valorPagamento = signal('');
  enviando = signal(false);
  mensagem = signal('');
  erro = signal('');

  ngOnInit(): void {
    const faturaId = this.route.snapshot.queryParamMap.get('fatura_id') ?? '';
    this.svc.detalheFatura(faturaId).subscribe({
      next: (f) => { this.fatura.set(f); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  pagar(): void {
    if (!this.valorPagamento()) return;
    this.enviando.set(true);
    this.mensagem.set('');
    this.erro.set('');
    const faturaId = this.route.snapshot.queryParamMap.get('fatura_id') ?? '';
    this.svc.pagarFatura(faturaId, parseFloat(this.valorPagamento())).subscribe({
      next: (res) => {
        this.mensagem.set(res.mensagem);
        this.fatura.update((f) => ({ ...f, valor_pago: res.valor_pago, valor_restante: res.valor_restante, status: res.status }));
        this.valorPagamento.set('');
        this.enviando.set(false);
      },
      error: (e) => {
        this.erro.set(e.error?.detail ?? 'Erro ao registrar pagamento.');
        this.enviando.set(false);
      },
    });
  }

  readonly statusCores: Record<string, string> = {
    aberta: '#3ba6f1', fechada: '#888',
    parcialmente_paga: '#f59e0b', paga: '#2f8f4e', vencida: '#e53e3e',
  };
}
