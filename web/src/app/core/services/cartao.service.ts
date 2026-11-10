/**
 * Serviço Angular para cartões de crédito e faturas.
 *
 * pq existe: Injectable do Angular centraliza as chamadas HTTP,
 *            evitando duplicação de lógica entre componentes.
 * para que no projeto: agrupa todos os métodos de cartão e fatura em um
 *                      único singleton injetável em qualquer componente.
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class CartaoService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listar(incluirArquivados = false): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/cartoes`, {
      params: { incluir_arquivados: String(incluirArquivados) },
    });
  }

  criar(dados: any): Observable<any> {
    return this.http.post(`${this.base}/cartoes`, dados);
  }

  atualizar(id: string, dados: any): Observable<any> {
    return this.http.put(`${this.base}/cartoes/${id}`, dados);
  }

  arquivar(id: string): Observable<any> {
    return this.http.delete(`${this.base}/cartoes/${id}`);
  }

  detalheFatura(faturaId: string): Observable<any> {
    return this.http.get(`${this.base}/faturas/${faturaId}`);
  }

  pagarFatura(faturaId: string, valor: number): Observable<any> {
    return this.http.post(`${this.base}/faturas/${faturaId}/pagar`, { valor });
  }

  historico(cartaoId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/faturas/cartao/${cartaoId}/historico`);
  }
}
