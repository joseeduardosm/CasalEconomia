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
  styleUrl: './painel.component.scss',
  template: `
    <div class="pagina">
      <div class="card">
        <div class="marca">CasalEconomia</div>
        <h1 class="titulo">Painel</h1>
        <p class="descricao">Em construção — autenticação funcionando.</p>
        <button class="botao-primario" (click)="sair()">Sair</button>
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
