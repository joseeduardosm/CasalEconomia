/**
 * Componente placeholder do painel principal.
 * Rota protegida por authGuard — destino após login/cadastro bem-sucedido.
 * O painel real será implementado na tarefa 09.
 */

import { Component } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-painel',
  standalone: true,
  template: `
    <div style="min-height:100vh;background:#fafaf9;display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;">
      <div style="background:#fff;border:1px solid #e8e6e5;border-radius:12px;padding:40px;max-width:440px;width:100%;text-align:center;">
        <div style="font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#3ba6f1;margin-bottom:16px;">CasalEconomia</div>
        <h1 style="font-size:22px;font-weight:500;color:#0c0a09;margin:0 0 8px;">Painel</h1>
        <p style="color:#78716c;font-size:14px;margin:0 0 24px;">Em construção — autenticação funcionando.</p>
        <button
          (click)="sair()"
          style="padding:10px 24px;background:#3ba6f1;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;"
        >
          Sair
        </button>
      </div>
    </div>
  `,
})
export class PainelComponent {
  constructor(private authService: AuthService) {}

  sair(): void {
    this.authService.sair();
  }
}
