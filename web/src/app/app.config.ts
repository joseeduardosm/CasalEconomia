/**
 * Configuração global da aplicação CasalEconomia.
 * Registra roteamento, cliente HTTP com interceptador de autenticação,
 * detecção de mudanças e ícones do sistema de design.
 *
 * pq existe: ApplicationConfig do Angular 19 substitui o AppModule —
 *            todos os provedores globais são declarados aqui de forma funcional.
 * para que no projeto: ponto único de registro de serviços globais;
 *                      provideIcons disponibiliza os ícones Heroicons em toda a árvore.
 */

import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideIcons } from '@ng-icons/core';
import {
  heroHome,
  heroDocumentText,
  heroBuildingLibrary,
  heroCreditCard,
  heroFlag,
  heroChartBar,
  heroUsers,
  heroCog6Tooth,
  heroArrowRightOnRectangle,
  heroNewspaper,
  heroArrowsRightLeft,
} from '@ng-icons/heroicons/outline';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideIcons({
      heroHome,
      heroDocumentText,
      heroBuildingLibrary,
      heroCreditCard,
      heroFlag,
      heroChartBar,
      heroUsers,
      heroCog6Tooth,
      heroArrowRightOnRectangle,
      heroNewspaper,
      heroArrowsRightLeft,
    }),
  ],
};
