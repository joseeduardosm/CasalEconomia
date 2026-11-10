/**
 * Configuração das rotas da aplicação CasalEconomia.
 * Rotas públicas ficam soltas; rotas autenticadas são filhas do ConchaComponent.
 *
 * pq existe: Routes do Angular define a árvore de navegação do SPA —
 *            o roteador interpreta a URL e renderiza o componente correto.
 * para que no projeto: agrupa todas as telas autenticadas sob ConchaComponent
 *                      (que fornece sidebar + barra superior); rotas públicas
 *                      (login, cadastro) ficam fora desse grupo.
 */

import { Routes } from '@angular/router';
import { ConchaComponent } from './layout/concha/concha.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/painel', pathMatch: 'full' },

  // Rotas públicas — sem AppShell
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'cadastro',
    loadComponent: () =>
      import('./features/auth/cadastro/cadastro.component').then((m) => m.CadastroComponent),
  },

  // Rotas autenticadas — dentro do AppShell (ConchaComponent)
  {
    path: '',
    component: ConchaComponent,
    canActivate: [authGuard],
    children: [
      {
        path: 'painel',
        data: { titulo: 'Painel' },
        loadComponent: () =>
          import('./features/painel/painel.component').then((m) => m.PainelComponent),
      },
      {
        path: 'lancamentos',
        data: { titulo: 'Lançamentos' },
        loadComponent: () =>
          import('./features/lancamentos/lancamentos.component').then((m) => m.LancamentosComponent),
      },
      {
        path: 'contas',
        data: { titulo: 'Contas' },
        loadComponent: () =>
          import('./features/contas/contas.component').then((m) => m.ContasComponent),
      },
      {
        path: 'cartoes',
        data: { titulo: 'Cartões' },
        loadComponent: () =>
          import('./features/cartoes/cartoes.component').then((m) => m.CartoesComponent),
      },
      {
        path: 'metas',
        data: { titulo: 'Metas' },
        loadComponent: () =>
          import('./features/metas/metas.component').then((m) => m.MetasComponent),
      },
      {
        path: 'relatorios',
        data: { titulo: 'Relatórios' },
        loadComponent: () =>
          import('./features/relatorios/relatorios.component').then((m) => m.RelatoriosComponent),
      },
      {
        path: 'casal',
        data: { titulo: 'Casal' },
        loadComponent: () =>
          import('./features/casal/casal.component').then((m) => m.CasalComponent),
      },
      {
        path: 'configuracoes',
        data: { titulo: 'Configurações' },
        loadComponent: () =>
          import('./features/configuracoes/configuracoes.component').then((m) => m.ConfiguracoesComponent),
      },
    ],
  },

  { path: '**', redirectTo: '/painel' },
];
