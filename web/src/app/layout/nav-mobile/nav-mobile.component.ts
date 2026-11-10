/**
 * Barra de navegação inferior para dispositivos móveis do CasalEconomia.
 * Exibe os 5 módulos principais com ícones, visível apenas em telas pequenas.
 *
 * pq existe: Angular standalone component com RouterLinkActive — detecta a rota
 *            ativa e aplica a classe de destaque sem lógica manual.
 * para que no projeto: substitui a sidebar em telas menores que 768px,
 *                      fixada na parte inferior da tela com os atalhos principais.
 */

import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgIconComponent } from '@ng-icons/core';

interface ItemMobile {
  rotulo: string;
  caminho: string;
  icone: string;
}

@Component({
  selector: 'app-nav-mobile',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgIconComponent],
  templateUrl: './nav-mobile.component.html',
  styleUrl: './nav-mobile.component.scss',
})
export class NavMobileComponent {
  readonly itens: ItemMobile[] = [
    { rotulo: 'Painel',      caminho: '/painel',      icone: 'heroHome' },
    { rotulo: 'Lançamentos', caminho: '/lancamentos', icone: 'heroDocumentText' },
    { rotulo: 'Contas',      caminho: '/contas',      icone: 'heroBuildingLibrary' },
    { rotulo: 'Cartões',     caminho: '/cartoes',     icone: 'heroCreditCard' },
    { rotulo: 'Casal',       caminho: '/casal',       icone: 'heroUsers' },
  ];
}
