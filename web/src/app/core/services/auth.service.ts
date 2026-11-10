/**
 * Serviço de autenticação do CasalEconomia.
 * Gerencia a ficha JWT no armazenamento local e expõe os métodos de sessão.
 *
 * pq existe: Injectable do Angular é um serviço singleton — uma única instância
 *            compartilhada por toda a aplicação via injeção de dependência.
 * para que no projeto: persiste a ficha JWT em localStorage, verifica autenticação
 *                      e realiza o logout navegando para /login.
 */

import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ParceiroService } from './parceiro.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly CHAVE_TOKEN = 'ce_token';
  private readonly roteador = inject(Router);
  private readonly parceiroService = inject(ParceiroService);

  salvarToken(token: string): void {
    localStorage.setItem(this.CHAVE_TOKEN, token);
  }

  getToken(): string | null {
    return localStorage.getItem(this.CHAVE_TOKEN);
  }

  estaAutenticado(): boolean {
    return !!this.getToken();
  }

  sair(): void {
    this.parceiroService.pararPolling();
    localStorage.removeItem(this.CHAVE_TOKEN);
    this.roteador.navigate(['/login']);
  }
}
