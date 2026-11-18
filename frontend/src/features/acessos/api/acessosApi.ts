import { api, apiListAll } from '../../../services/api'
import type { GrupoAcesso, Permissao, PermissaoCatalogo } from '../../../types'

export interface DadosDoGrupo {
  nome: string
  descricao: string | null
  permissoes: Permissao[]
}

export function listarGruposDeAcesso() {
  return apiListAll<GrupoAcesso>('/api/grupos-acesso')
}

export function listarPermissoes() {
  return apiListAll<PermissaoCatalogo>('/api/permissoes')
}

export function criarGrupo(dados: DadosDoGrupo) {
  return api('/api/grupos-acesso', { method: 'POST', body: JSON.stringify(dados) })
}

export function atualizarGrupo(id: number, dados: DadosDoGrupo) {
  return api(`/api/grupos-acesso/${id}`, { method: 'PUT', body: JSON.stringify(dados) })
}

export function excluirGrupo(id: number) {
  return api(`/api/grupos-acesso/${id}`, { method: 'DELETE' })
}
