/**
 * Configuração global da aplicação CasalEconomia.
 * Registra roteamento, HttpClient com interceptor de autenticação e change detection.
 */

import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    // Registra HttpClient com o interceptor funcional de autenticação
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};
