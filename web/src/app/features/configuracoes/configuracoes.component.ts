/**
 * Tela de configurações do CasalEconomia — inclui geração de convite de casal.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: permite ao usuário autenticado convidar seu parceiro
 *                      gerando um link único de acesso.
 */

import { Component, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-configuracoes',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './configuracoes.component.html',
  styleUrl: './configuracoes.component.scss',
})
export class ConfiguracoesComponent {
  private http = inject(HttpClient);

  nomeConvidado = signal('');
  emailConvidado = signal('');
  linkGerado = signal('');
  enviando = signal(false);
  erro = signal('');
  copiado = signal(false);

  gerarConvite(): void {
    if (!this.nomeConvidado() || !this.emailConvidado()) return;
    this.enviando.set(true);
    this.erro.set('');
    this.linkGerado.set('');

    this.http
      .post<{ token: string; nome_convidado: string; email_convidado: string }>(
        `${environment.apiUrl}/convites`,
        { nome_convidado: this.nomeConvidado(), email_convidado: this.emailConvidado() }
      )
      .subscribe({
        next: (res) => {
          const origem = window.location.origin;
          this.linkGerado.set(`${origem}/convite/${res.token}`);
          this.enviando.set(false);
        },
        error: (e) => {
          this.erro.set(e.error?.detail ?? 'Erro ao gerar convite.');
          this.enviando.set(false);
        },
      });
  }

  copiarLink(): void {
    navigator.clipboard.writeText(this.linkGerado()).then(() => {
      this.copiado.set(true);
      setTimeout(() => this.copiado.set(false), 2000);
    });
  }
}
