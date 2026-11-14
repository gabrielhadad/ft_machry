import type { ReactNode } from 'react'
import { EstoquePage } from '../pages/Estoque/EstoquePage'
import { FichasPage } from '../pages/Fichas/FichasPage'
import { InicioPage } from '../pages/Inicio/InicioPage'
import { LocalizacoesPage } from '../pages/Localizacoes/LocalizacoesPage'
import { MovimentacoesPage } from '../pages/Movimentacoes/MovimentacoesPage'
import { ProducaoPage } from '../pages/Producao/ProducaoPage'
import { ProdutosPage } from '../pages/Produtos/ProdutosPage'
import { UsuariosPage } from '../pages/Usuarios/UsuariosPage'
import type { Dados, Mutacao, Recurso } from '../stores/dados'
import type { FichaTecnica, PapelUsuario, Usuario } from '../types'

export type View = 'inicio' | 'produtos' | 'fichas' | 'estoque' | 'producao' | 'historico' | 'locais' | 'usuarios'

export interface ContextoDaPagina {
  usuario: Usuario
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
  papeis: PapelUsuario[]
  recursos: (usuario: Usuario) => Recurso[]
  pagina: (contexto: ContextoDaPagina) => ReactNode
}

const todos: PapelUsuario[] = ['OWNER', 'ADMIN', 'USER']
const gestao: PapelUsuario[] = ['OWNER', 'ADMIN']
const proprietaria: PapelUsuario[] = ['OWNER']

const ehProprietaria = (usuario: Usuario) => usuario.papel === 'OWNER'
const ehGestao = (usuario: Usuario) => usuario.papel !== 'USER'

export const rotas: Rota[] = [
  {
    view: 'inicio',
    caminho: '/',
    titulo: 'Visão geral',
    icone: '⌂',
    papeis: gestao,
    recursos: () => ['produtos', 'fichas', 'lotes'],
    pagina: ({ usuario, dados, abrirFicha }) => <InicioPage
      produtos={dados.produtos}
      fichas={dados.fichas}
      lotes={dados.lotes}
      canManage={ehProprietaria(usuario)}
      onNewSheet={() => abrirFicha('new')}
      onViewSheet={abrirFicha}
    />,
  },
  {
    view: 'produtos',
    caminho: '/produtos',
    titulo: 'Produtos',
    icone: '◫',
    papeis: proprietaria,
    recursos: () => ['produtos'],
    pagina: ({ dados, aoAlterar }) => <ProdutosPage produtos={dados.produtos} aoAlterar={aoAlterar} />,
  },
  {
    view: 'fichas',
    caminho: '/fichas',
    titulo: 'Fichas técnicas',
    icone: '≡',
    papeis: todos,
    recursos: () => ['fichas'],
    pagina: ({ usuario, dados, abrirFicha, aoAlterar }) => <FichasPage
      fichas={dados.fichas}
      canManage={ehProprietaria(usuario)}
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
    papeis: gestao,
    recursos: () => ['lotes', 'produtos', 'localizacoes'],
    pagina: ({ usuario, dados, aoAlterar }) => <EstoquePage
      lotes={dados.lotes}
      produtos={dados.produtos}
      localizacoes={dados.localizacoes}
      usuarioId={usuario.id}
      onChanged={(mensagem) => aoAlterar('estoque', mensagem)}
    />,
  },
  {
    view: 'producao',
    caminho: '/producao',
    titulo: 'Produção',
    icone: '◉',
    papeis: todos,
    recursos: (usuario) => ehGestao(usuario)
      ? ['solicitacoes', 'fichas', 'produtos', 'localizacoes']
      : ['solicitacoes', 'fichas'],
    pagina: ({ usuario, dados, abrirFicha, aoAlterar, avisarErro }) => <ProducaoPage
      solicitacoes={dados.solicitacoes}
      fichas={dados.fichas}
      produtos={dados.produtos}
      localizacoes={dados.localizacoes}
      canPlan={ehGestao(usuario)}
      onViewSheet={abrirFicha}
      aoAlterar={aoAlterar}
      avisarErro={avisarErro}
    />,
  },
  {
    view: 'historico',
    caminho: '/movimentacoes',
    titulo: 'Movimentações',
    icone: '↺',
    papeis: gestao,
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
    papeis: gestao,
    recursos: () => ['localizacoes'],
    pagina: ({ dados, atualizar }) => <LocalizacoesPage localizacoes={dados.localizacoes} atualizar={atualizar} />,
  },
  {
    view: 'usuarios',
    caminho: '/usuarios',
    titulo: 'Usuários',
    icone: '♙',
    papeis: proprietaria,
    recursos: () => [],
    pagina: ({ usuario, rodadaDeAtualizacao }) => <UsuariosPage usuarioLogado={usuario} rodadaDeAtualizacao={rodadaDeAtualizacao} />,
  },
]

export function rotaDaView(view: View): Rota {
  return rotas.find((rota) => rota.view === view) ?? rotas[0]
}

export function rotasDoUsuario(usuario: Usuario): Rota[] {
  return rotas.filter((rota) => rota.papeis.includes(usuario.papel))
}

export function podeAcessar(rota: Rota, usuario: Usuario) {
  return rota.papeis.includes(usuario.papel)
}

export function viewInicial(usuario: Usuario): View {
  return ehGestao(usuario) ? 'inicio' : 'producao'
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
