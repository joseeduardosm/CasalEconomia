/**
 * Dados estáticos do changelog do CasalEconomia.
 * Atualizar a cada nova versão lançada, espelhando o CHANGELOG.md.
 *
 * pq existe: TypeScript const exportada — fonte única de verdade para o
 *            componente de changelog; evita parsear Markdown em runtime.
 * para que no projeto: alimenta a tela /changelog com as entradas do diário
 *                      de versões, agrupadas por data de lançamento.
 */

export interface EntradaChangelog {
  versao: string;
  data: string;         // ISO "YYYY-MM-DD"
  titulo: string;
  adicionado: string[];
  alterado: string[];
  corrigido: string[];
}

export const ENTRADAS_CHANGELOG: EntradaChangelog[] = [
  {
    versao: '0.3.0',
    data: '2026-11-10',
    titulo: 'Navegação e AppShell',
    adicionado: [
      'ConchaComponent (AppShell) com layout flex responsivo para desktop e mobile',
      'NavLateralComponent — sidebar de 220px com 8 módulos, item ativo em ciano e logout no rodapé',
      'BarraTopoComponent — 56px, título dinâmico via rota e seletor de período "‹ Nov 2026 ›"',
      'NavMobileComponent — barra inferior fixa para telas menores que 768px',
      'PeriodoService — signal mesAtivo com computed labelPeriodo',
      '7 telas placeholder com carregamento tardio: Lançamentos, Contas, Cartões, Metas, Relatórios, Casal, Configurações',
      'Ícones Heroicons via @ng-icons/core v29.10.0 (compatível com Angular 19)',
      'Convenção de cabeçalho "pq existe / para que no projeto" em todos os arquivos',
    ],
    alterado: [
      'PainelComponent — botão de logout removido (agora na sidebar)',
      'app.routes.ts — rotas autenticadas migradas para filhas de ConchaComponent',
      'Comentários do projeto convertidos para PT-BR puro',
    ],
    corrigido: [],
  },
  {
    versao: '0.2.0',
    data: '2026-11-10',
    titulo: 'Autenticação JWT',
    adicionado: [
      'Autenticação completa com JWT (HS256, expiração de 7 dias)',
      'Tabela users com UUID, nome, e-mail único e senha em hash bcrypt — criada via migração Alembic',
      'Rotas POST /auth/registrar (201) e POST /auth/entrar (200)',
      'Repositório usuario.py com buscar_por_email e criar',
      'Esquemas Pydantic: EntradaCadastro, EntradaLogin, RespostaToken',
      'Serviço auth.py com gerar_token, verificar_token, gerar_hash_senha e verificar_senha',
      'AuthService Angular singleton com salvarToken, getToken, estaAutenticado e sair',
      'authInterceptor funcional — injeta a ficha JWT em todas as requisições autenticadas',
      'authGuard funcional — redireciona para /login se não autenticado',
      'Telas de login e cadastro com design Seline Analytics',
    ],
    alterado: [],
    corrigido: [
      'Downgrade de bcrypt para 4.0.1 para compatibilidade com passlib 1.7.4',
      'Adicionado pydantic[email] ao requirements.txt para suporte a EmailStr',
    ],
  },
  {
    versao: '0.1.0',
    data: '2026-11-10',
    titulo: 'Estrutura base do projeto',
    adicionado: [
      'Estrutura base do projeto: api/, web/, nginx/',
      'API FastAPI com instância aplicacao, CORS configurado e rota GET /saude',
      'database.py com motor, FabricaSessao, Base e obter_sessao() em PT-BR',
      'requirements.txt com FastAPI 0.115, SQLAlchemy 2, Alembic 1.13, Pydantic 2.9',
      'Alembic inicializado e env.py configurado para ler DATABASE_URL do .env',
      'Projeto Angular 19 com roteamento e SCSS',
      'nginx.conf para proxy reverso: /api/ → porta 8000, / → porta 4200',
      'Banco de dados casaleconomia_dev criado no PostgreSQL 16',
      'Serviços systemd casaleconomia-api e casaleconomia-web com inicialização automática',
      '.gitignore cobrindo Python, Node e arquivos de ambiente (.env)',
    ],
    alterado: [],
    corrigido: [],
  },
];

/** Agrupa as entradas por data, do mais recente para o mais antigo. */
export interface DiaChangelog {
  data: string;
  dataFormatada: string;
  versoes: EntradaChangelog[];
}

export function agruparPorDia(entradas: EntradaChangelog[]): DiaChangelog[] {
  const mapa = new Map<string, EntradaChangelog[]>();
  for (const entrada of entradas) {
    const lista = mapa.get(entrada.data) ?? [];
    lista.push(entrada);
    mapa.set(entrada.data, lista);
  }

  return Array.from(mapa.entries())
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([data, versoes]) => ({
      data,
      dataFormatada: new Date(data + 'T12:00:00')
        .toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }),
      versoes,
    }));
}
