/**
 * Guard de autenticação.
 * Redireciona para /login se o usuário não estiver autenticado.
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
