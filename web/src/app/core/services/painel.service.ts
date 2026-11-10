/**
 * Serviço Angular para o endpoint agregado do painel.
 *
 * pq existe: Injectable do Angular centraliza as chamadas HTTP do painel,
 *            evitando que o componente se preocupe com URLs.
 * para que no projeto: carrega todos os dados do dashboard em um único request
 *                      e delega aceitar/ignorar pendentes ao endpoint do parceiro.
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class PainelService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  carregar(mes: string): Observable<any> {
    return this.http.get(`${this.base}/painel`, { params: { mes } });
  }

  aceitarPendente(id: string, versaoEsperada: number): Observable<any> {
    return this.http.post(`${this.base}/parceiro/${id}/aceitar`, { versao_esperada: versaoEsperada });
  }

  ignorarPendente(id: string, versaoEsperada: number): Observable<any> {
    return this.http.post(`${this.base}/parceiro/${id}/ignorar`, { versao_esperada: versaoEsperada });
  }
}
