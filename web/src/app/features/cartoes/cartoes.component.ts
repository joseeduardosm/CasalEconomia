/**
 * Tela de listagem de cartões de crédito do CasalEconomia.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: exibe grid de cartões com fatura atual, limite disponível
 *                      e status; permite criar novo cartão via formulário inline.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CartaoService } from '../../core/services/cartao.service';

@Component({
  selector: 'app-cartoes',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, FormsModule],
  templateUrl: './cartoes.component.html',
  styleUrl: './cartoes.component.scss',
})
export class CartoesComponent implements OnInit {
  private svc = inject(CartaoService);
  private router = inject(Router);

  cartoes = signal<any[]>([]);
  carregando = signal(true);
  mostrarFormulario = signal(false);
  enviando = signal(false);
  erro = signal('');

  nome = signal('');
  bandeira = signal('mastercard');
  limite = signal('');
  diaFechamento = signal(3);
  diaVencimento = signal(10);
  cor = signal('#3ba6f1');

  readonly statusCores: Record<string, string> = {
    aberta: '#3ba6f1',
    fechada: '#888',
    parcialmente_paga: '#f59e0b',
    paga: '#2f8f4e',
    vencida: '#e53e3e',
  };

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.svc.listar().subscribe({
      next: (lista) => { this.cartoes.set(lista); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  criarCartao(): void {
    this.enviando.set(true);
    this.svc.criar({
      nome: this.nome(),
      bandeira: this.bandeira(),
      limite: parseFloat(this.limite()),
      dia_fechamento: this.diaFechamento(),
      dia_vencimento: this.diaVencimento(),
      cor: this.cor(),
    }).subscribe({
      next: () => {
        this.mostrarFormulario.set(false);
        this.enviando.set(false);
        this.carregar();
      },
      error: (e: any) => {
        this.erro.set(e.error?.detail ?? 'Erro ao criar cartão.');
        this.enviando.set(false);
      },
    });
  }

  verFatura(item: any): void {
    if (item.fatura_atual?.fatura_id) {
      this.router.navigate(['/cartoes', item.cartao.id, 'fatura'], {
        queryParams: { fatura_id: item.fatura_atual.fatura_id },
      });
    }
  }

  statusRotulo(status: string): string {
    const mapa: Record<string, string> = {
      aberta: 'Aberta',
      fechada: 'Fechada',
      parcialmente_paga: 'Parcial',
      paga: 'Paga',
      vencida: 'Vencida',
    };
    return mapa[status] ?? status;
  }
}
