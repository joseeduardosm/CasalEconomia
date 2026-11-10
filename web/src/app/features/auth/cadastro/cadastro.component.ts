/**
 * Tela de cadastro do CasalEconomia.
 * Formulário com nome, e-mail e senha; após sucesso navega para /painel.
 *
 * pq existe: ReactiveFormsModule do Angular gerencia formulários com validação
 *            e estado declarativos, sem manipulação direta do DOM.
 * para que no projeto: criação de nova conta — coleta dados do usuário,
 *                      chama /api/auth/registrar e persiste a ficha JWT recebida.
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
