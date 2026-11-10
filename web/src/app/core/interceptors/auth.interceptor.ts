/**
 * Interceptador HTTP de autenticação do CasalEconomia.
 * Injeta o cabeçalho de autorização em todas as requisições autenticadas.
 *
 * pq existe: HttpInterceptorFn do Angular intercepta todas as requisições HTTP
 *            da aplicação antes de enviá-las, permitindo modificação centralizada.
 * para que no projeto: adiciona automaticamente o cabeçalho "Authorization: Bearer <ficha>"
 *                      em cada chamada à API, sem precisar repetir em cada serviço.
 */

import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(req);
};
