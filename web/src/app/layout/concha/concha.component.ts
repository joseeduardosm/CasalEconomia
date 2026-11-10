/**
 * AppShell da aplicação CasalEconomia — layout com topbar horizontal.
 *
 * pq existe: Angular standalone component que envolve todas as rotas autenticadas.
 * para que no projeto: renderiza a topbar fixa + router-outlet + nav mobile;
 *                      sem sidebar — navegação fica na barra superior como no openmonetis.
 */

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BarraTopoComponent } from '../barra-topo/barra-topo.component';
import { NavMobileComponent } from '../nav-mobile/nav-mobile.component';

@Component({
  selector: 'app-concha',
  standalone: true,
  imports: [RouterOutlet, BarraTopoComponent, NavMobileComponent],
  templateUrl: './concha.component.html',
  styleUrl: './concha.component.scss',
})
export class ConchaComponent {}
