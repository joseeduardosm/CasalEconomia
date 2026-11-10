/**
 * AppShell da aplicação CasalEconomia.
 * Envolve todas as rotas autenticadas com o layout de duas colunas.
 *
 * pq existe: Angular standalone component — unidade de UI autossuficiente,
 *            sem NgModule, que declara suas próprias dependências via imports[].
 * para que no projeto: estrutura raiz do layout autenticado — renderiza sidebar,
 *                      barra superior, router-outlet e navegação mobile em conjunto.
 */

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavLateralComponent } from '../nav-lateral/nav-lateral.component';
import { BarraTopoComponent } from '../barra-topo/barra-topo.component';
import { NavMobileComponent } from '../nav-mobile/nav-mobile.component';

@Component({
  selector: 'app-concha',
  standalone: true,
  imports: [RouterOutlet, NavLateralComponent, BarraTopoComponent, NavMobileComponent],
  templateUrl: './concha.component.html',
  styleUrl: './concha.component.scss',
})
export class ConchaComponent {}
