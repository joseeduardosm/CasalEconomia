/**
 * Serviço de autenticação do CasalEconomia.
 * Gerencia o token JWT no localStorage e expõe os métodos de sessão do usuário.
 */

import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly CHAVE_TOKEN = 'ce_token';
  private readonly roteador = inject(Router);

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
    localStorage.removeItem(this.CHAVE_TOKEN);
    this.roteador.navigate(['/login']);
  }
}
