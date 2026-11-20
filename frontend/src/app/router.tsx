import type { ReactNode } from 'react'
import { EstoquePage } from '../pages/Estoque/EstoquePage'
import { FichasPage } from '../pages/Fichas/FichasPage'
import { GruposDeAcessoPage } from '../pages/GruposDeAcesso/GruposDeAcessoPage'
import { InicioPage } from '../pages/Inicio/InicioPage'
import { LocalizacoesPage } from '../pages/Localizacoes/LocalizacoesPage'
import { MovimentacoesPage } from '../pages/Movimentacoes/MovimentacoesPage'
import { PracasPage } from '../pages/Pracas/PracasPage'
import { ProducaoPage } from '../pages/Producao/ProducaoPage'
import { ProdutosPage } from '../pages/Produtos/ProdutosPage'
import { UsuariosPage } from '../pages/Usuarios/UsuariosPage'
import type { Dados, Mutacao, Recurso } from '../stores/dados'
import type { FichaTecnica, Permissao, UsuarioLogado } from '../types'
import { temPermissao, temTodas } from '../utils/permissoes'
import { podeCriarFicha, podePlanejarProducao } from './regrasDeAcesso'

export type View =
  | 'inicio'
  | 'produtos'
  | 'fichas'
  | 'estoque'
  | 'producao'
  | 'pracas'
  | 'historico'
  | 'locais'
  | 'usuarios'
  | 'grupos'

export interface ContextoDaPagina {
  usuario: UsuarioLogado
  dados: Dados
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
  atualizar: (mutacao: Mutacao) => Promise<boolean>
  abrirFicha: (ficha: FichaTecnica | 'new') => void
  avisarErro: (mensagem: string) => void
  rodadaDeAtualizacao: number
}

export interface Rota {
  view: View
  caminho: string
  titulo: string
  icone: string
  permissoes: Permissao[]
  recursos: (usuario: UsuarioLogado) => Recurso[]
  pagina: (contexto: ContextoDaPagina) => ReactNode
}

export const rotas: Rota[] = [
  {
    view: 'inicio',
    caminho: '/',
    titulo: 'Visão geral',
    icone: '⌂',
    permissoes: ['produtos:ler', 'fichas_tecnicas:ler', 'estoque:ler'],
    recursos: () => ['produtos', 'fichas', 'lotes'],
    pagina: ({ usuario, dados, abrirFicha }) => <InicioPage
      produtos={dados.produtos}
      fichas={dados.fichas}
      lotes={dados.lotes}
      canManage={podeCriarFicha(usuario)}
      onNewSheet={() => abrirFicha('new')}
      onViewSheet={abrirFicha}
    />,
  },
  {
    view: 'produtos',
    caminho: '/produtos',
    titulo: 'Produtos',
    icone: '◫',
    permissoes: ['produtos:ler'],
    recursos: () => ['produtos'],
    pagina: ({ usuario, dados, aoAlterar }) => <ProdutosPage
      produtos={dados.produtos}
      podeCriar={temPermissao(usuario, 'produtos:criar')}
      podeEditar={temPermissao(usuario, 'produtos:atualizar')}
      podeExcluir={temPermissao(usuario, 'produtos:excluir')}
      aoAlterar={aoAlterar}
    />,
  },
  {
    view: 'fichas',
    caminho: '/fichas',
    titulo: 'Fichas técnicas',
    icone: '≡',
    permissoes: ['fichas_tecnicas:ler'],
    recursos: () => ['fichas'],
    pagina: ({ usuario, dados, abrirFicha, aoAlterar }) => <FichasPage
      fichas={dados.fichas}
      canManage={podeCriarFicha(usuario)}
      onNew={() => abrirFicha('new')}
      onView={abrirFicha}
      aoAlterar={aoAlterar}
    />,
  },
  {
    view: 'estoque',
    caminho: '/estoque',
    titulo: 'Estoque',
    icone: '▦',
    permissoes: ['estoque:ler', 'produtos:ler', 'localizacoes:ler'],
    recursos: () => ['lotes', 'produtos', 'localizacoes'],
    pagina: ({ usuario, dados, aoAlterar }) => <EstoquePage
      lotes={dados.lotes}
      produtos={dados.produtos}
      localizacoes={dados.localizacoes}
      usuarioId={usuario.id}
      podeCriar={temPermissao(usuario, 'estoque:criar')}
      podeEditar={temPermissao(usuario, 'estoque:atualizar')}
      onChanged={(mensagem) => aoAlterar('estoque', mensagem)}
    />,
  },
  {
    view: 'producao',
    caminho: '/producao',
    titulo: 'Produção',
    icone: '◉',
    permissoes: ['producao:ler', 'fichas_tecnicas:ler'],
    recursos: (usuario) => [
      'solicitacoes', 'fichas',
      ...(podePlanejarProducao(usuario) ? (['produtos', 'localizacoes'] as Recurso[]) : []),
      ...(temPermissao(usuario, 'pracas:ler') ? (['pracas'] as Recurso[]) : []),
    ],
    pagina: ({ usuario, dados, abrirFicha, aoAlterar, avisarErro }) => <ProducaoPage
      solicitacoes={dados.solicitacoes}
      fichas={dados.fichas}
      produtos={dados.produtos}
      localizacoes={dados.localizacoes}
      pracas={dados.pracas}
      podeConsultarPracas={temPermissao(usuario, 'pracas:ler')}
      canPlan={podePlanejarProducao(usuario)}
      podeAtualizar={temPermissao(usuario, 'producao:atualizar')}
      onViewSheet={abrirFicha}
      aoAlterar={aoAlterar}
      avisarErro={avisarErro}
    />,
  },
  {
    view: 'pracas',
    caminho: '/pracas',
    titulo: 'Praças',
    icone: '♧',
    permissoes: ['pracas:ler'],
    recursos: () => ['pracas'],
    pagina: ({ usuario, dados, aoAlterar, rodadaDeAtualizacao }) => <PracasPage
      pracas={dados.pracas}
      podeCriar={temPermissao(usuario, 'pracas:criar')}
      podeAtualizar={temPermissao(usuario, 'pracas:atualizar')}
      podeExcluir={temPermissao(usuario, 'pracas:excluir')}
      aoAlterar={aoAlterar}
      rodadaDeAtualizacao={rodadaDeAtualizacao}
    />,
  },
  {
    view: 'historico',
    caminho: '/movimentacoes',
    titulo: 'Movimentações',
    icone: '↺',
    permissoes: ['estoque:ler', 'produtos:ler'],
    recursos: () => ['lotes', 'produtos'],
    pagina: ({ dados, rodadaDeAtualizacao }) => <MovimentacoesPage
      lotes={dados.lotes}
      produtos={dados.produtos}
      rodadaDeAtualizacao={rodadaDeAtualizacao}
    />,
  },
  {
    view: 'locais',
    caminho: '/localizacoes',
    titulo: 'Localizações',
    icone: '▤',
    permissoes: ['localizacoes:ler'],
    recursos: () => ['localizacoes'],
    pagina: ({ usuario, dados, atualizar }) => <LocalizacoesPage
      localizacoes={dados.localizacoes}
      podeCriar={temPermissao(usuario, 'localizacoes:criar')}
      podeAtualizar={temPermissao(usuario, 'localizacoes:atualizar')}
      podeExcluir={temPermissao(usuario, 'localizacoes:excluir')}
      atualizar={atualizar}
    />,
  },
  {
    view: 'usuarios',
    caminho: '/usuarios',
    titulo: 'Usuários',
    icone: '♙',
    permissoes: ['usuarios:ler'],
    recursos: () => [],
    pagina: ({ usuario, rodadaDeAtualizacao }) => <UsuariosPage
      usuarioLogado={usuario}
      rodadaDeAtualizacao={rodadaDeAtualizacao}
    />,
  },
  {
    view: 'grupos',
    caminho: '/grupos-acesso',
    titulo: 'Grupos de acesso',
    icone: '◈',
    permissoes: ['grupos_acesso:ler'],
    recursos: () => [],
    pagina: ({ usuario, rodadaDeAtualizacao }) => <GruposDeAcessoPage
      usuarioLogado={usuario}
      rodadaDeAtualizacao={rodadaDeAtualizacao}
    />,
  },
]

const viewsPreferidasParaEntrar: View[] = ['inicio', 'producao']

export function rotaDaView(view: View): Rota {
  return rotas.find((rota) => rota.view === view) ?? rotas[0]
}

export function podeAcessar(rota: Rota, usuario: UsuarioLogado) {
  return temTodas(usuario, rota.permissoes)
}

export function rotasDoUsuario(usuario: UsuarioLogado): Rota[] {
  return rotas.filter((rota) => podeAcessar(rota, usuario))
}

export function viewInicial(usuario: UsuarioLogado): View {
  const liberadas = rotasDoUsuario(usuario)
  const preferida = viewsPreferidasParaEntrar.find(
    (view) => liberadas.some((rota) => rota.view === view),
  )
  return preferida ?? liberadas[0]?.view ?? 'inicio'
}

function caminhoAtual() {
  const caminho = window.location.pathname
  if (caminho.length > 1 && caminho.endsWith('/')) return caminho.slice(0, -1)
  return caminho
}

export function viewDaUrl(): View | null {
  const rota = rotas.find((item) => item.caminho === caminhoAtual())
  return rota ? rota.view : null
}

export function escreverNaUrl(view: View, modo: 'novo' | 'substituir') {
  const caminho = rotaDaView(view).caminho
  if (caminhoAtual() === caminho) return
  if (modo === 'novo') window.history.pushState(null, '', caminho)
  else window.history.replaceState(null, '', caminho)
}
