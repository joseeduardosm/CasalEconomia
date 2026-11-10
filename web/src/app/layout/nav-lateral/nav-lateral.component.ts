/**
 * Sidebar de navegação principal do CasalEconomia.
 * Lista os módulos do app com ícones, destaca o item ativo e exibe badge de pendentes.
 *
 * pq existe: Angular standalone component com RouterLinkActive — diretiva que
 *            aplica CSS automaticamente à rota correspondente à URL atual.
 * para que no projeto: barra lateral fixa de 220px com os módulos do sistema;
 *                      item Parceiro exibe badge com contagem de pendências.
 */

import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';
import { AuthService } from '../../core/services/auth.service';
import { ParceiroService } from '../../core/services/parceiro.service';

interface ItemMenu {
  rotulo: string;
  caminho: string;
  icone: string;
  badge?: boolean;
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
  readonly parceiro = inject(ParceiroService);

  readonly itensMenu: ItemMenu[] = [
    { rotulo: 'Painel',        caminho: '/painel',               icone: 'heroHome' },
    { rotulo: 'Lançamentos',   caminho: '/lancamentos',          icone: 'heroDocumentText' },
    { rotulo: 'Parceiro',      caminho: '/lancamentos-parceiro', icone: 'heroArrowsRightLeft', badge: true },
    { rotulo: 'Contas',        caminho: '/contas',               icone: 'heroBuildingLibrary' },
    { rotulo: 'Cartões',       caminho: '/cartoes',              icone: 'heroCreditCard' },
    { rotulo: 'Metas',         caminho: '/metas',                icone: 'heroFlag' },
    { rotulo: 'Relatórios',    caminho: '/relatorios',           icone: 'heroChartBar' },
    { rotulo: 'Casal',         caminho: '/casal',                icone: 'heroUsers' },
    { rotulo: 'Configurações', caminho: '/configuracoes',        icone: 'heroCog6Tooth' },
    { rotulo: 'Changelog',     caminho: '/changelog',            icone: 'heroNewspaper' },
  ];

  sair(): void {
    this.authService.sair();
  }
}
