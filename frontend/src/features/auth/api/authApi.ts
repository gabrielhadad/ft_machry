import { api } from '../../../services/api'
import type { Usuario } from '../../../types'

export function entrar(username: string, password: string) {
  return api<Usuario>('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
}

export function sair() {
  return api('/api/auth/logout', { method: 'POST' })
}

export function buscarUsuarioLogado() {
  return api<Usuario>('/api/auth/me')
}
