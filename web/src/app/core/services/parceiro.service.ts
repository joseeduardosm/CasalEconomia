/**
 * Serviço de pendências do parceiro no CasalEconomia.
 * Gerencia polling periódico do badge de lançamentos pendentes.
 *
 * pq existe: Angular Injectable com signals — estado reativo compartilhado
 *            entre componentes sem Subject/BehaviorSubject.
 * para que no projeto: mantém a contagem de pendências atualizada na sidebar
 *                      via poll a cada 30 segundos enquanto o usuário está logado.
 */

import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ParceiroService {
  private http = inject(HttpClient);

  readonly totalPendentes = signal(0);
  private intervaloId: ReturnType<typeof setInterval> | null = null;

  iniciarPolling(): void {
    this.buscarContagem();
    this.intervaloId = setInterval(() => this.buscarContagem(), 30_000);
  }

  pararPolling(): void {
    if (this.intervaloId !== null) {
      clearInterval(this.intervaloId);
      this.intervaloId = null;
    }
    this.totalPendentes.set(0);
  }

  buscarContagem(): void {
    this.http
      .get<{ total: number }>(`${environment.apiUrl}/parceiro/pendentes/contagem`)
      .subscribe({ next: (r) => this.totalPendentes.set(r.total), error: () => {} });
  }
}
