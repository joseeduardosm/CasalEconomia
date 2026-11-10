/**
 * Serviço Angular para lançamentos financeiros.
 *
 * pq existe: Injectable do Angular centraliza as chamadas HTTP,
 *            evitando duplicação de lógica entre componentes.
 * para que no projeto: agrupa listagem, criação, edição, exclusão
 *                      e importação XLSX de lançamentos.
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class LancamentosService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listar(filtros: { mes?: string; cartao_id?: string; liquidado?: boolean } = {}): Observable<any[]> {
    const params: any = {};
    if (filtros.mes) params['mes'] = filtros.mes;
    if (filtros.cartao_id) params['cartao_id'] = filtros.cartao_id;
    if (filtros.liquidado !== undefined) params['liquidado'] = String(filtros.liquidado);
    return this.http.get<any[]>(`${this.base}/lancamentos`, { params });
  }

  criar(dados: any): Observable<any> {
    return this.http.post(`${this.base}/lancamentos`, dados);
  }

  atualizar(id: string, dados: any, escopo: 'individual' | 'serie' = 'individual'): Observable<any> {
    return this.http.put(`${this.base}/lancamentos/${id}`, dados, { params: { escopo } });
  }

  excluir(id: string, escopo: 'individual' | 'serie' = 'individual'): Observable<any> {
    return this.http.delete(`${this.base}/lancamentos/${id}`, { params: { escopo } });
  }

  baixarModelo(): void {
    this.http.get(`${this.base}/lancamentos/modelo-importacao`, { responseType: 'blob' }).subscribe((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'modelo-lancamentos.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  validarImportacao(arquivo: File): Observable<any> {
    const form = new FormData();
    form.append('arquivo', arquivo);
    return this.http.post(`${this.base}/lancamentos/importar`, form);
  }

  confirmarImportacao(linhas: any[]): Observable<any> {
    return this.http.post(`${this.base}/lancamentos/importar/confirmar`, { linhas });
  }

  criarReceita(dados: any): Observable<any> {
    return this.http.post(`${this.base}/lancamentos`, { ...dados, tipo: 'receita' });
  }

  marcarRecebido(id: string, valorRecebido?: number): Observable<any> {
    const body: any = { liquidado: true };
    if (valorRecebido !== undefined) body['valor_recebido'] = valorRecebido;
    return this.http.put(`${this.base}/lancamentos/${id}`, body);
  }
}
