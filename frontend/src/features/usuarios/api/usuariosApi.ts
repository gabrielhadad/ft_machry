import { api, apiListAll } from '../../../services/api'
import type { PapelUsuario, Usuario } from '../../../types'

export interface NovoUsuario {
  nome: string
  username: string
  password: string
  papel: PapelUsuario
}

export interface AlteracaoDoUsuario {
  nome: string
  papel: PapelUsuario
  ativo: number
  password?: string
}

export function listarUsuarios() {
  return apiListAll<Usuario>('/api/usuarios')
}

export function criarUsuario(dados: NovoUsuario) {
  return api('/api/usuarios', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarUsuario(id: number, dados: AlteracaoDoUsuario) {
  return api(`/api/usuarios/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}
