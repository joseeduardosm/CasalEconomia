/**
 * Tela de lançamentos pendentes do parceiro no CasalEconomia.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: exibe a fila de lançamentos aguardando ação do usuário
 *                      (aceitar ou ignorar), atualizando o badge após cada ação.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { environment } from '../../../environments/environment';
import { ParceiroService } from '../../core/services/parceiro.service';

interface Pendente {
  id: string;
  snapshot_descricao: string;
  snapshot_valor: number;
  snapshot_data: string;
  snapshot_tipo: string;
  versao_fonte: number;
  usuario_dono_id: string;
  processando?: boolean;
}

@Component({
  selector: 'app-lancamentos-parceiro',
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './lancamentos-parceiro.component.html',
  styleUrl: './lancamentos-parceiro.component.scss',
})
export class LancamentosParceiroComponent implements OnInit {
  private http = inject(HttpClient);
  private parceiro = inject(ParceiroService);

  pendentes = signal<Pendente[]>([]);
  carregando = signal(true);

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.http.get<Pendente[]>(`${environment.apiUrl}/parceiro/pendentes`).subscribe({
      next: (lista) => { this.pendentes.set(lista); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  aceitar(item: Pendente): void {
    this.processar(item, 'aceitar');
  }

  ignorar(item: Pendente): void {
    this.processar(item, 'ignorar');
  }

  private processar(item: Pendente, acao: 'aceitar' | 'ignorar'): void {
    item.processando = true;
    this.pendentes.update((lista) => [...lista]);
    this.http
      .post(`${environment.apiUrl}/parceiro/${item.id}/${acao}`, { versao_esperada: item.versao_fonte })
      .subscribe({
        next: () => {
          this.pendentes.update((lista) => lista.filter((p) => p.id !== item.id));
          this.parceiro.buscarContagem();
        },
        error: () => {
          item.processando = false;
          this.pendentes.update((lista) => [...lista]);
        },
      });
  }
}
