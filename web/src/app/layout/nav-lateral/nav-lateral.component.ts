/**
 * Sidebar de navegação principal do CasalEconomia.
 * Lista os módulos do app com ícones e destaca o item ativo.
 *
 * pq existe: Angular standalone component com RouterLinkActive — diretiva que
 *            aplica CSS automaticamente à rota correspondente à URL atual.
 * para que no projeto: barra lateral fixa de 220px que agrupa os 8 módulos do
 *                      sistema; item ativo destacado em ciano; logout no rodapé.
 */

import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';
import { AuthService } from '../../core/services/auth.service';

interface ItemMenu {
  rotulo: string;
  caminho: string;
  icone: string;
}

@Component({
  selector: 'app-nav-lateral',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgIconComponent],
  templateUrl: './nav-lateral.component.html',
  styleUrl: './nav-lateral.component.scss',
})
export class NavLateralComponent {
  private readonly authService = inject(AuthService);

  readonly itensMenu: ItemMenu[] = [
    { rotulo: 'Painel',        caminho: '/painel',        icone: 'heroHome' },
    { rotulo: 'Lançamentos',   caminho: '/lancamentos',   icone: 'heroDocumentText' },
    { rotulo: 'Contas',        caminho: '/contas',        icone: 'heroBuildingLibrary' },
    { rotulo: 'Cartões',       caminho: '/cartoes',       icone: 'heroCreditCard' },
    { rotulo: 'Metas',         caminho: '/metas',         icone: 'heroFlag' },
    { rotulo: 'Relatórios',    caminho: '/relatorios',    icone: 'heroChartBar' },
    { rotulo: 'Casal',         caminho: '/casal',         icone: 'heroUsers' },
    { rotulo: 'Configurações', caminho: '/configuracoes', icone: 'heroCog6Tooth' },
  ];

  sair(): void {
    this.authService.sair();
  }
}
