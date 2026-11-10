/**
 * Componente de cadastro do CasalEconomia.
 * Formulário reativo com nome, e-mail e senha.
 * Após sucesso salva o token e navega para /painel.
 * Exibe erro PT-BR quando o e-mail já estiver cadastrado (HTTP 400).
 */

import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

interface RespostaToken {
  access_token: string;
  tipo_token: string;
}

@Component({
  selector: 'app-cadastro',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CommonModule],
  templateUrl: './cadastro.component.html',
  styleUrl: './cadastro.component.scss',
})
export class CadastroComponent {
  formulario: FormGroup;
  mensagemErro = '';
  carregando = false;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private authService: AuthService,
    private router: Router,
  ) {
    this.formulario = this.fb.group({
      nome: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      senha: ['', [Validators.required, Validators.minLength(4)]],
    });
  }

  enviar(): void {
    if (this.formulario.invalid) return;

    this.carregando = true;
    this.mensagemErro = '';

    this.http
      .post<RespostaToken>(`${environment.apiUrl}/auth/registrar`, this.formulario.value)
      .subscribe({
        next: (resposta) => {
          this.authService.salvarToken(resposta.access_token);
          this.router.navigate(['/painel']);
        },
        error: (err) => {
          if (err.status === 400) {
            this.mensagemErro = 'Este e-mail já está cadastrado. Tente fazer login.';
          } else {
            this.mensagemErro = 'Ocorreu um erro ao criar a conta. Tente novamente.';
          }
          this.carregando = false;
        },
      });
  }
}
