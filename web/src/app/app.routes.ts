/**
 * Configuração das rotas da aplicação CasalEconomia.
 * Rotas de autenticação são públicas; /painel é protegida pelo authGuard.
 */

import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/login/login.component';
import { CadastroComponent } from './features/auth/cadastro/cadastro.component';
import { PainelComponent } from './features/painel/painel.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // Redireciona a raiz para login
  { path: '', redirectTo: '/login', pathMatch: 'full' },

  // Rotas públicas
  { path: 'login', component: LoginComponent },
  { path: 'cadastro', component: CadastroComponent },

  // Rota protegida — authGuard redireciona para /login se não autenticado
  { path: 'painel', component: PainelComponent, canActivate: [authGuard] },

  // Qualquer URL desconhecida vai para login
  { path: '**', redirectTo: '/login' },
];
