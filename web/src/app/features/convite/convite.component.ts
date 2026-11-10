/**
 * Tela pública de aceitação de convite do CasalEconomia.
 * Lê o token da URL, busca os dados do convidado e permite cadastro.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS,
 *            carregado de forma lazy via loadComponent.
 * para que no projeto: única tela fora do AppShell que permite a um novo
 *                      usuário criar conta a partir de um convite com token UUID.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-convite',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './convite.component.html',
  styleUrl: './convite.component.scss',
})
export class ConviteComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);

  token = signal('');
  nomeConvidado = signal('');
  emailConvidado = signal('');
  senha = signal('');
  carregando = signal(true);
  enviando = signal(false);
  erro = signal('');
  naoEncontrado = signal(false);

  ngOnInit(): void {
    const t = this.route.snapshot.paramMap.get('token') ?? '';
    this.token.set(t);
    this.http.get<{ nome: string; email: string }>(`${environment.apiUrl}/convites/${t}`).subscribe({
      next: (dados) => {
        this.nomeConvidado.set(dados.nome);
        this.emailConvidado.set(dados.email);
        this.carregando.set(false);
      },
      error: () => {
        this.naoEncontrado.set(true);
        this.carregando.set(false);
      },
    });
  }

  aceitar(): void {
    if (!this.senha()) return;
    this.enviando.set(true);
    this.erro.set('');
    this.http
      .post(`${environment.apiUrl}/convites/${this.token()}/aceitar`, { senha: this.senha() })
      .subscribe({
        next: () => this.router.navigate(['/login'], { queryParams: { cadastro: 'sucesso' } }),
        error: (e) => {
          this.erro.set(e.error?.detail ?? 'Erro ao aceitar o convite.');
          this.enviando.set(false);
        },
      });
  }
}
