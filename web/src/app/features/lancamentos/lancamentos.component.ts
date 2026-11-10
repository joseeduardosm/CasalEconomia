/**
 * Tela de lançamentos financeiros do mês ativo.
 *
 * pq existe: Angular standalone component com signals — reativo sem RxJS.
 * para que no projeto: lista despesas e receitas agrupadas por data, com filtros
 *                      de tipo, chips de status de receita, FAB expansível,
 *                      modal de criação separado por tipo e importação XLSX.
 */

import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LancamentosService } from '../../core/services/lancamentos.service';
import { CartaoService } from '../../core/services/cartao.service';
import { PeriodoService } from '../../core/services/periodo.service';

interface Lancamento {
  id: string;
  descricao: string;
  valor: number;
  data_lancamento: string;
  tipo: string;
  forma_pagamento?: string;
  liquidado?: boolean;
  parcela_atual?: number;
  serie_id?: string;
  email_compartilhado?: string;
  categoria?: string;
  status_receita?: string;
  valor_recebido?: number;
  fonte?: string;
}

@Component({
  selector: 'app-lancamentos',
  standalone: true,
  imports: [CurrencyPipe, DatePipe, FormsModule],
  templateUrl: './lancamentos.component.html',
  styleUrl: './lancamentos.component.scss',
})
export class LancamentosComponent implements OnInit {
  private svc = inject(LancamentosService);
  private cartaoSvc = inject(CartaoService);
  private periodoSvc = inject(PeriodoService);

  lancamentos = signal<Lancamento[]>([]);
  cartoes = signal<any[]>([]);
  carregando = signal(true);

  // Filtro de tipo
  filtroTipo = signal<'todos' | 'despesa' | 'receita'>('todos');

  // FAB expansível
  fabAberto = signal(false);

  // Modal criar despesa
  modalCriar = signal(false);
  enviandoCriar = signal(false);
  erroCriar = signal('');
  descricao = signal('');
  dataLancamento = signal(new Date().toISOString().split('T')[0]);
  valor = signal('');
  parcelado = signal(false);
  totalParcelas = signal(2);
  parcelaInicio = signal(1);
  formaPagamento = signal('');
  cartaoId = signal('');
  liquidado = signal(false);
  categoria = signal('');
  nota = signal('');
  emailCompartilhado = signal('');
  percentualCompartilhado = signal(50);

  // Modal criar receita
  modalCriarReceita = signal(false);
  enviandoCriarReceita = signal(false);
  erroCriarReceita = signal('');
  descricaoReceita = signal('');
  dataReceita = signal(new Date().toISOString().split('T')[0]);
  valorReceita = signal('');
  fonteReceita = signal('');
  categoriaReceita = signal('');
  notaReceita = signal('');
  liquidadoReceita = signal(false);
  valorRecebidoReceita = signal('');

  // Modal importar
  modalImportar = signal(false);
  etapaImportar = signal<1 | 2>(1);
  carregandoImportar = signal(false);
  linhasValidas = signal<any[]>([]);
  linhasComErro = signal<any[]>([]);
  enviandoImportar = signal(false);

  readonly agrupados = computed(() => {
    const filtro = this.filtroTipo();
    const lista = filtro === 'todos'
      ? this.lancamentos()
      : this.lancamentos().filter(l => l.tipo === filtro);
    const grupos: Record<string, Lancamento[]> = {};
    for (const l of lista) {
      if (!grupos[l.data_lancamento]) grupos[l.data_lancamento] = [];
      grupos[l.data_lancamento].push(l);
    }
    return Object.entries(grupos).sort(([a], [b]) => b.localeCompare(a));
  });

  ngOnInit(): void {
    this.carregar();
    this.cartaoSvc.listar().subscribe({ next: (lista) => this.cartoes.set(lista) });
  }

  carregar(): void {
    this.carregando.set(true);
    const p = this.periodoSvc.mesAtivo();
    const mes = `${p.ano.toString().padStart(4, '0')}-${p.mes.toString().padStart(2, '0')}`;
    this.svc.listar({ mes }).subscribe({
      next: (lista) => { this.lancamentos.set(lista); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  abrirCriarDespesa(): void {
    this.resetarFormulario();
    this.modalCriar.set(true);
    this.fabAberto.set(false);
  }

  abrirCriarReceita(): void {
    this.resetarFormularioReceita();
    this.modalCriarReceita.set(true);
    this.fabAberto.set(false);
  }

  salvar(continuarDepois: boolean): void {
    this.enviandoCriar.set(true);
    this.erroCriar.set('');
    this.svc.criar({
      descricao: this.descricao(),
      data_lancamento: this.dataLancamento(),
      valor: parseFloat(this.valor()),
      tipo: 'despesa',
      forma_pagamento: this.formaPagamento() || null,
      cartao_id: this.cartaoId() || null,
      liquidado: this.formaPagamento() === 'cartao_credito' ? null : this.liquidado(),
      categoria: this.categoria() || null,
      nota: this.nota() || null,
      parcelado: this.parcelado(),
      total_parcelas: this.parcelado() ? this.totalParcelas() : null,
      parcela_inicio: this.parcelaInicio(),
      email_compartilhado: this.emailCompartilhado() || null,
      percentual_compartilhado: this.emailCompartilhado() ? this.percentualCompartilhado() : null,
    }).subscribe({
      next: () => {
        this.enviandoCriar.set(false);
        this.carregar();
        if (continuarDepois) {
          this.descricao.set('');
          this.valor.set('');
          this.parcelado.set(false);
          this.dataLancamento.set(new Date().toISOString().split('T')[0]);
        } else {
          this.modalCriar.set(false);
          this.resetarFormulario();
        }
      },
      error: (e: any) => {
        this.erroCriar.set(e.error?.detail ?? 'Erro ao salvar.');
        this.enviandoCriar.set(false);
      },
    });
  }

  salvarReceita(continuarDepois: boolean): void {
    this.enviandoCriarReceita.set(true);
    this.erroCriarReceita.set('');
    this.svc.criarReceita({
      descricao: this.descricaoReceita(),
      data_lancamento: this.dataReceita(),
      valor: parseFloat(this.valorReceita()),
      fonte: this.fonteReceita() || null,
      categoria: this.categoriaReceita() || null,
      nota: this.notaReceita() || null,
      liquidado: this.liquidadoReceita(),
      valor_recebido: this.liquidadoReceita() && this.valorRecebidoReceita()
        ? parseFloat(this.valorRecebidoReceita())
        : null,
    }).subscribe({
      next: () => {
        this.enviandoCriarReceita.set(false);
        this.carregar();
        if (continuarDepois) {
          this.descricaoReceita.set('');
          this.valorReceita.set('');
          this.dataReceita.set(new Date().toISOString().split('T')[0]);
          this.liquidadoReceita.set(false);
          this.valorRecebidoReceita.set('');
        } else {
          this.modalCriarReceita.set(false);
          this.resetarFormularioReceita();
        }
      },
      error: (e: any) => {
        this.erroCriarReceita.set(e.error?.detail ?? 'Erro ao salvar receita.');
        this.enviandoCriarReceita.set(false);
      },
    });
  }

  marcarRecebido(item: Lancamento): void {
    this.svc.marcarRecebido(item.id).subscribe({ next: () => this.carregar() });
  }

  excluir(id: string): void {
    if (!confirm('Excluir este lançamento?')) return;
    this.svc.excluir(id).subscribe({ next: () => this.carregar() });
  }

  resetarFormulario(): void {
    this.descricao.set(''); this.valor.set('');
    this.dataLancamento.set(new Date().toISOString().split('T')[0]);
    this.parcelado.set(false); this.totalParcelas.set(2); this.parcelaInicio.set(1);
    this.formaPagamento.set(''); this.cartaoId.set('');
    this.liquidado.set(false); this.categoria.set(''); this.nota.set('');
    this.emailCompartilhado.set(''); this.percentualCompartilhado.set(50);
    this.erroCriar.set('');
  }

  resetarFormularioReceita(): void {
    this.descricaoReceita.set(''); this.valorReceita.set('');
    this.dataReceita.set(new Date().toISOString().split('T')[0]);
    this.fonteReceita.set(''); this.categoriaReceita.set(''); this.notaReceita.set('');
    this.liquidadoReceita.set(false); this.valorRecebidoReceita.set('');
    this.erroCriarReceita.set('');
  }

  onArquivoSelecionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    this.carregandoImportar.set(true);
    this.svc.validarImportacao(input.files[0]).subscribe({
      next: (res) => {
        this.linhasValidas.set(res.linhas_validas);
        this.linhasComErro.set(res.linhas_com_erro);
        this.etapaImportar.set(2);
        this.carregandoImportar.set(false);
      },
      error: () => this.carregandoImportar.set(false),
    });
  }

  confirmarImportacao(): void {
    this.enviandoImportar.set(true);
    this.svc.confirmarImportacao(this.linhasValidas()).subscribe({
      next: () => {
        this.modalImportar.set(false);
        this.etapaImportar.set(1);
        this.enviandoImportar.set(false);
        this.carregar();
      },
      error: () => this.enviandoImportar.set(false),
    });
  }

  baixarModelo(): void {
    this.svc.baixarModelo();
  }

  valorParceiro(): number {
    return parseFloat(this.valor() || '0') * this.percentualCompartilhado() / 100;
  }

  podeMarcarRecebido(item: Lancamento): boolean {
    return item.tipo === 'receita'
      && (item.status_receita === 'previsto' || item.status_receita === 'a_receber');
  }

  labelStatusReceita(status?: string): string {
    const mapa: Record<string, string> = {
      previsto: 'Previsto',
      a_receber: 'A receber',
      parcialmente_recebido: 'Parcial',
      recebido: 'Recebido',
    };
    return status ? (mapa[status] ?? status) : '';
  }

  get mostrarParcelamento(): boolean {
    return this.formaPagamento() === 'cartao_credito' || this.formaPagamento() === 'boleto';
  }

  get mostrarCartao(): boolean {
    return this.formaPagamento() === 'cartao_credito';
  }
}
