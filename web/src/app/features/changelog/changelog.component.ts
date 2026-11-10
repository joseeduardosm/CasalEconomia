/**
 * Tela de changelog do CasalEconomia — diário de versões.
 * Exibe as atualizações do sistema agrupadas por data, sem dias vazios.
 *
 * pq existe: Angular standalone component com sinais e computed —
 *            estado reativo sem RxJS, re-renderização mínima.
 * para que no projeto: permite ao usuário acompanhar o histórico de
 *                      melhorias do app como se fosse um diário,
 *                      navegando entre as datas pelo menu lateral.
 */

import { Component, computed, signal } from '@angular/core';
import { ENTRADAS_CHANGELOG, DiaChangelog, agruparPorDia } from './changelog.data';

@Component({
  selector: 'app-changelog',
  standalone: true,
  templateUrl: './changelog.component.html',
  styleUrl: './changelog.component.scss',
})
export class ChangelogComponent {
  readonly dias = computed<DiaChangelog[]>(() => agruparPorDia(ENTRADAS_CHANGELOG));
  readonly diaAtivo = signal<string>(this.dias()[0]?.data ?? '');

  irPara(data: string): void {
    this.diaAtivo.set(data);
    const el = document.getElementById('dia-' + data);
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
