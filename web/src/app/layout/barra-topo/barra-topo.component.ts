/**
 * Topbar principal do CasalEconomia — substitui a sidebar por navegação horizontal.
 *
 * pq existe: header fixo no topo, igual ao openmonetis-v2.
 * para que no projeto: logo + links de navegação desktop + seletor de período
 *                      + botão de logout; mobile expõe apenas logo + período.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { filter } from 'rxjs/operators';
import { NgIconComponent } from '@ng-icons/core';
import { AuthService } from '../../core/services/auth.service';
import { ParceiroService } from '../../core/services/parceiro.service';
import { PeriodoService } from '../../core/services/periodo.service';

interface ItemNav {
  rotulo: string;
  caminho: string;
  icone: string;
  badge?: boolean;
}

@Component({
  selector: 'app-barra-topo',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgIconComponent],
  templateUrl: './barra-topo.component.html',
  styleUrl: './barra-topo.component.scss',
})
export class BarraTopoComponent implements OnInit {
  readonly periodo = inject(PeriodoService);
  readonly parceiro = inject(ParceiroService);
  private readonly auth = inject(AuthService);
  private readonly roteador = inject(Router);

  menuAberto = signal(false);

  readonly itensNav: ItemNav[] = [
    { rotulo: 'Painel',       caminho: '/painel',               icone: 'heroHome' },
    { rotulo: 'Lançamentos',  caminho: '/lancamentos',          icone: 'heroDocumentText' },
    { rotulo: 'Cartões',      caminho: '/cartoes',              icone: 'heroCreditCard' },
    { rotulo: 'Casal',        caminho: '/casal',                icone: 'heroUsers' },
    { rotulo: 'Metas',        caminho: '/metas',                icone: 'heroFlag' },
    { rotulo: 'Relatórios',   caminho: '/relatorios',           icone: 'heroChartBar' },
  ];

  readonly itensMais: ItemNav[] = [
    { rotulo: 'Parceiro',      caminho: '/lancamentos-parceiro', icone: 'heroArrowsRightLeft', badge: true },
    { rotulo: 'Contas',        caminho: '/contas',               icone: 'heroBuildingLibrary' },
    { rotulo: 'Configurações', caminho: '/configuracoes',        icone: 'heroCog6Tooth' },
    { rotulo: 'Changelog',     caminho: '/changelog',            icone: 'heroNewspaper' },
  ];

  ngOnInit(): void {
    this.roteador.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe(() => this.menuAberto.set(false));
  }

  sair(): void {
    this.auth.sair();
  }

  toggleMenu(): void {
    this.menuAberto.update(v => !v);
  }

  fecharMenu(): void {
    this.menuAberto.set(false);
  }
}
