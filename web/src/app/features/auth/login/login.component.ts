/**
 * Tela de login do CasalEconomia.
 * Formulário com e-mail e senha; em caso de sucesso navega para /painel.
 *
 * pq existe: ReactiveFormsModule do Angular gerencia formulários com validação
 *            e estado declarativos, sem manipulação direta do DOM.
 * para que no projeto: ponto de entrada da sessão autenticada — coleta credenciais,
 *                      chama /api/auth/entrar e persiste a ficha JWT recebida.
 */

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

interface RespostaToken {
  access_token: string;
  tipo_token: string;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {
  formulario: FormGroup;
  mensagemErro = '';
  mensagemSucesso = '';
  carregando = false;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
  ) {
    this.formulario = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      senha: ['', Validators.required],
    });
  }

  ngOnInit(): void {
    if (this.route.snapshot.queryParamMap.get('cadastro') === 'sucesso') {
      this.mensagemSucesso = 'Cadastro realizado! Faça login para continuar.';
    }
  }

  enviar(): void {
    if (this.formulario.invalid) return;

    this.carregando = true;
    this.mensagemErro = '';

    this.http
      .post<RespostaToken>(`${environment.apiUrl}/auth/entrar`, this.formulario.value)
      .subscribe({
        next: (resposta) => {
          this.authService.salvarToken(resposta.access_token);
          this.router.navigate(['/painel']);
        },
        error: () => {
          this.mensagemErro = 'E-mail ou senha inválidos. Verifique e tente novamente.';
          this.carregando = false;
        },
      });
  }
}
