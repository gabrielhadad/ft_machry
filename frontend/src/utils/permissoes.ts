import type { Permissao, UsuarioLogado } from '../types'

export function temPermissao(usuario: UsuarioLogado, permissao: Permissao) {
  return usuario.permissoes.includes(permissao)
}

export function temTodas(usuario: UsuarioLogado, permissoes: Permissao[]) {
  return permissoes.every((permissao) => temPermissao(usuario, permissao))
}
