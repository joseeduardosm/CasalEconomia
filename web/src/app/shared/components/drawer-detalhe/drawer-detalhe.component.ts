/**
 * Drawer lateral reutilizável para exibir detalhes de lançamentos.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: painel lateral deslizante que aparece ao clicar em
 *                      qualquer widget do painel, exibindo tabela ordenável
 *                      ou detalhe individual de um lançamento.
 */

import {
  Component, Input, Output, EventEmitter, OnInit, OnChanges,
  inject, signal, computed,
} from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import { LancamentosService } from '../../../core/services/lancamentos.service';

export interface FiltroDrawer {
  titulo: string;
  mes?: string;
  tipo?: string;
  liquidado?: boolean;
  cartao_id?: string;
  lancamento?: any;
}

@Component({
  selector: 'app-drawer-detalhe',
  standalone: true,
  imports: [CurrencyPipe, DatePipe],
  templateUrl: './drawer-detalhe.component.html',
  styleUrl: './drawer-detalhe.component.scss',
})
export class DrawerDetalheComponent implements OnInit, OnChanges {
  @Input({ required: true }) filtro!: FiltroDrawer;
  @Output() fechar = new EventEmitter<void>();

  private svc = inject(LancamentosService);
  private router = inject(Router);

  itens = signal<any[]>([]);
  carregando = signal(true);

  ordemColuna = signal<string>('data_lancamento');
  ordemDesc = signal(true);

  readonly itensSorted = computed(() => {
    const col = this.ordemColuna();
    const desc = this.ordemDesc();
    return [...this.itens()].sort((a, b) => {
      const va = a[col] ?? '';
      const vb = b[col] ?? '';
      return desc ? (vb > va ? 1 : -1) : (va > vb ? 1 : -1);
    });
  });

  readonly total = computed(() =>
    this.itens().reduce((acc, l) => acc + (parseFloat(l.valor) || 0), 0)
  );

  ngOnInit(): void {
    this.carregar();
  }

  ngOnChanges(): void {
    this.carregar();
  }

  carregar(): void {
    if (this.filtro.lancamento) {
      this.itens.set([this.filtro.lancamento]);
      this.carregando.set(false);
      return;
    }
    this.carregando.set(true);
    const params: any = {};
    if (this.filtro.mes) params['mes'] = this.filtro.mes;
    if (this.filtro.tipo) params['tipo'] = this.filtro.tipo;
    if (this.filtro.liquidado !== undefined) params['liquidado'] = this.filtro.liquidado;
    if (this.filtro.cartao_id) params['cartao_id'] = this.filtro.cartao_id;

    this.svc.listar(params).subscribe({
      next: (lista) => { this.itens.set(lista); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  ordenarPor(col: string): void {
    if (this.ordemColuna() === col) {
      this.ordemDesc.set(!this.ordemDesc());
    } else {
      this.ordemColuna.set(col);
      this.ordemDesc.set(true);
    }
  }

  verTodosEmLancamentos(): void {
    const params: any = {};
    if (this.filtro.mes) params['mes'] = this.filtro.mes;
    this.router.navigate(['/lancamentos'], { queryParams: params });
    this.fechar.emit();
  }

  get ehDetalheUnico(): boolean {
    return !!this.filtro.lancamento;
  }

  indicadorOrdem(col: string): string {
    if (this.ordemColuna() !== col) return '';
    return this.ordemDesc() ? ' ↓' : ' ↑';
  }
}
