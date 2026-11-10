/**
 * Tela do painel principal do CasalEconomia.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: dashboard central que agrega resumo do mês, faturas,
 *                      vencimentos, lançamentos recentes e dados do parceiro
 *                      em um único carregamento via GET /painel.
 */

import { Component, OnDestroy, inject, signal, computed, effect } from '@angular/core';
import { CurrencyPipe, DatePipe, TitleCasePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { PainelService } from '../../core/services/painel.service';
import { PeriodoService } from '../../core/services/periodo.service';
import { DrawerDetalheComponent } from '../../shared/components/drawer-detalhe/drawer-detalhe.component';

@Component({
  selector: 'app-painel',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, TitleCasePipe, RouterLink, DrawerDetalheComponent],
  templateUrl: './painel.component.html',
  styleUrl: './painel.component.scss',
})
export class PainelComponent implements OnDestroy {
  private svc = inject(PainelService);
  private periodoSvc = inject(PeriodoService);

  dados = signal<any | null>(null);
  carregando = signal(true);
  drawerFiltro = signal<any | null>(null);
  aceitando = signal<Record<string, boolean>>({});
  ignorando = signal<Record<string, boolean>>({});

  readonly mes = computed(() => {
    const p = this.periodoSvc.mesAtivo();
    return `${p.ano.toString().padStart(4, '0')}-${p.mes.toString().padStart(2, '0')}`;
  });

  readonly primeiroNome = computed(() => {
    const nome = this.dados()?.usuario_nome ?? '';
    return nome.trim().split(/\s+/)[0] || 'você';
  });

  readonly saudacao = computed(() => {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
  });

  readonly dataFormatada = computed(() => {
    return new Date().toLocaleDateString('pt-BR', {
      weekday: 'long', day: 'numeric', month: 'long',
    });
  });

  /* Itens para a faixa de atenção — faturas vencendo + vencimentos urgentes + pendentes */
  readonly itensAtencao = computed(() => {
    const d = this.dados();
    if (!d) return [];
    const lista: any[] = [];

    // Faturas vencendo em breve
    for (const f of d.faturas_abertas ?? []) {
      if (f.vencendo_em_breve) {
        lista.push({
          id: `fatura-${f.fatura_id}`,
          tipo_label: 'Fatura',
          titulo: f.cartao_nome,
          detalhe: `Vence ${f.data_vencimento ? new Date(f.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR') : ''}`,
          valor: f.valor_restante,
          critico: true,
        });
      }
    }

    // Lançamentos vencidos
    for (const v of d.proximos_vencimentos ?? []) {
      if (v.vencido) {
        lista.push({
          id: `venc-${v.id}`,
          tipo_label: 'Vencido',
          titulo: v.descricao,
          detalhe: `Venceu em ${new Date(v.data_vencimento + 'T00:00:00').toLocaleDateString('pt-BR')}`,
          valor: v.valor,
          critico: true,
        });
      } else if (v.dias_para_vencer <= 3) {
        lista.push({
          id: `venc-${v.id}`,
          tipo_label: 'Vencendo',
          titulo: v.descricao,
          detalhe: v.dias_para_vencer === 0 ? 'Vence hoje' : `Vence em ${v.dias_para_vencer} dias`,
          valor: v.valor,
          critico: false,
        });
      }
    }

    // Pendentes do parceiro
    for (const p of d.parceiro?.pendentes ?? []) {
      lista.push({
        id: `parceiro-${p.id}`,
        tipo_label: 'Parceiro',
        titulo: p.snapshot_descricao,
        detalhe: 'Aguardando aprovação',
        valor: p.snapshot_valor,
        critico: false,
      });
    }

    return lista.slice(0, 8);
  });

  private efeito = effect(() => {
    this.carregar(this.mes());
  });

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

  labelVencimento(item: any): string {
    if (item.vencido) return 'Vencido';
    if (item.dias_para_vencer === 0) return 'Vence hoje';
    if (item.dias_para_vencer === 1) return 'Vence amanhã';
    return `Vence em ${item.dias_para_vencer} dias`;
  }

  aceitar(pendente: any): void {
    this.aceitando.update(s => ({ ...s, [pendente.id]: true }));
    this.svc.aceitarPendente(pendente.id, pendente.versao_fonte).subscribe({
      next: () => { this.aceitando.update(s => ({ ...s, [pendente.id]: false })); this.carregar(); },
      error: () => this.aceitando.update(s => ({ ...s, [pendente.id]: false })),
    });
  }

  ignorar(pendente: any): void {
    this.ignorando.update(s => ({ ...s, [pendente.id]: true }));
    this.svc.ignorarPendente(pendente.id, pendente.versao_fonte).subscribe({
      next: () => { this.ignorando.update(s => ({ ...s, [pendente.id]: false })); this.carregar(); },
      error: () => this.ignorando.update(s => ({ ...s, [pendente.id]: false })),
    });
  }
}
