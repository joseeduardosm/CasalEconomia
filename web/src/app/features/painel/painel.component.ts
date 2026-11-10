/**
 * Tela do painel principal do CasalEconomia.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: dashboard central que agrega resumo do mês, faturas,
 *                      vencimentos, lançamentos recentes e dados do parceiro
 *                      em um único carregamento via GET /painel.
 */

import { Component, OnInit, OnDestroy, inject, signal, computed, effect } from '@angular/core';
import { PainelService } from '../../core/services/painel.service';
import { PeriodoService } from '../../core/services/periodo.service';
import { ResumoMesComponent } from './components/resumo-mes.component';
import { FaturasCardComponent } from './components/faturas-card.component';
import { LancamentosRecentesComponent } from './components/lancamentos-recentes.component';
import { ProximosVencimentosComponent } from './components/proximos-vencimentos.component';
import { WidgetParceiroComponent } from './components/widget-parceiro.component';
import { DrawerDetalheComponent } from '../../shared/components/drawer-detalhe/drawer-detalhe.component';

@Component({
  selector: 'app-painel',
  standalone: true,
  imports: [
    ResumoMesComponent,
    FaturasCardComponent,
    LancamentosRecentesComponent,
    ProximosVencimentosComponent,
    WidgetParceiroComponent,
    DrawerDetalheComponent,
  ],
  templateUrl: './painel.component.html',
  styleUrl: './painel.component.scss',
})
export class PainelComponent implements OnInit, OnDestroy {
  private svc = inject(PainelService);
  private periodoSvc = inject(PeriodoService);

  dados = signal<any | null>(null);
  carregando = signal(true);

  drawerFiltro = signal<any | null>(null);

  readonly mes = computed(() => {
    const p = this.periodoSvc.mesAtivo();
    return `${p.ano.toString().padStart(4, '0')}-${p.mes.toString().padStart(2, '0')}`;
  });

  private efeito = effect(() => {
    const m = this.mes();
    this.carregar(m);
  });

  ngOnInit(): void {}

  ngOnDestroy(): void {
    this.efeito.destroy();
  }

  carregar(mes?: string): void {
    this.carregando.set(true);
    this.svc.carregar(mes ?? this.mes()).subscribe({
      next: (d) => { this.dados.set(d); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  abrirDrawer(filtro: any): void {
    this.drawerFiltro.set({ ...filtro, mes: filtro.mes ?? this.mes() });
  }

  fecharDrawer(): void {
    this.drawerFiltro.set(null);
  }
}
