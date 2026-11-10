/**
 * Barra superior da aplicação CasalEconomia.
 * Exibe o título da tela atual e o seletor de período financeiro.
 *
 * pq existe: Router.events do Angular emite eventos a cada mudança de rota;
 *            NavigationEnd permite ler os dados (data) da rota ativa.
 * para que no projeto: lê o título de cada rota via data.titulo e exibe ao lado
 *                      do seletor de mês/ano que controla o período financeiro.
 */

import { Component, OnInit, inject, signal } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';
import { PeriodoService } from '../../core/services/periodo.service';

@Component({
  selector: 'app-barra-topo',
  standalone: true,
  imports: [],
  templateUrl: './barra-topo.component.html',
  styleUrl: './barra-topo.component.scss',
})
export class BarraTopoComponent implements OnInit {
  readonly periodo = inject(PeriodoService);
  private readonly roteador = inject(Router);

  readonly tituloPagina = signal('');

  ngOnInit(): void {
    this.atualizarTitulo();
    this.roteador.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe(() => this.atualizarTitulo());
  }

  private atualizarTitulo(): void {
    let rota = this.roteador.routerState.snapshot.root;
    while (rota.firstChild) rota = rota.firstChild;
    this.tituloPagina.set(rota.data['titulo'] ?? '');
  }
}
