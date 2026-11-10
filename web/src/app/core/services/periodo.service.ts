/**
 * Serviço de período financeiro ativo do CasalEconomia.
 * Expõe o mês/ano selecionado como signal reativo para toda a aplicação.
 *
 * pq existe: Angular Signals permitem estado reativo sem RxJS — mudanças propagam
 *            automaticamente para todos os componentes que consomem o signal.
 * para que no projeto: centraliza o mês/ano que filtra lançamentos, contas e metas;
 *                      BarraTopoComponent escreve, telas financeiras leem.
 */

import { Injectable, computed, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PeriodoService {
  readonly mesAtivo = signal<{ mes: number; ano: number }>({
    mes: new Date().getMonth() + 1,
    ano: new Date().getFullYear(),
  });

  readonly labelPeriodo = computed(() => {
    const { mes, ano } = this.mesAtivo();
    return new Date(ano, mes - 1)
      .toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
      .replace('.', '')
      .replace(/^\w/, (c) => c.toUpperCase());
  });

  irParaMesAnterior(): void {
    this.mesAtivo.update(({ mes, ano }) => {
      if (mes === 1) return { mes: 12, ano: ano - 1 };
      return { mes: mes - 1, ano };
    });
  }

  irParaMesSeguinte(): void {
    this.mesAtivo.update(({ mes, ano }) => {
      if (mes === 12) return { mes: 1, ano: ano + 1 };
      return { mes: mes + 1, ano };
    });
  }
}
