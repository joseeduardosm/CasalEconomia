/**
 * Componente raiz da aplicação CasalEconomia.
 * Ponto de entrada do Angular — apenas encapsula o router-outlet principal.
 *
 * pq existe: Todo app Angular precisa de um componente raiz declarado no
 *            bootstrap do main.ts que sirva de âncora para o roteador.
 * para que no projeto: wrapper transparente — todo o layout real fica no
 *                      ConchaComponent (rotas autenticadas) ou nos componentes de auth.
 */

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {}
