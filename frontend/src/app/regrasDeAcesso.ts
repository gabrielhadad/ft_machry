import type { UsuarioLogado } from '../types'
import { temPermissao, temTodas } from '../utils/permissoes'

export function podeCriarFicha(usuario: UsuarioLogado) {
  return temTodas(usuario, ['fichas_tecnicas:criar', 'produtos:ler'])
}

export function podeEditarFicha(usuario: UsuarioLogado) {
  return temTodas(usuario, ['fichas_tecnicas:atualizar', 'produtos:ler'])
}

export function podeExcluirFicha(usuario: UsuarioLogado) {
  return temPermissao(usuario, 'fichas_tecnicas:excluir')
}

export function podePlanejarProducao(usuario: UsuarioLogado) {
  return temTodas(usuario, ['producao:criar', 'produtos:ler', 'localizacoes:ler'])
}
