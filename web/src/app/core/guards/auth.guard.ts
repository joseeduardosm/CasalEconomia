/**
 * Protetor de rota de autenticação do CasalEconomia.
 * Bloqueia acesso às telas protegidas se o usuário não estiver autenticado.
 *
 * pq existe: CanActivateFn do Angular é uma função protetora de rota —
 *            executada pelo roteador antes de renderizar qualquer componente filho.
 * para que no projeto: impede acesso direto via URL às telas do AppShell;
 *                      redireciona para /login quando não há ficha válida.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const roteador = inject(Router);

  if (authService.estaAutenticado()) {
    return true;
  }

  return roteador.createUrlTree(['/login']);
};
