import type { Permissao } from './acesso'

export interface GrupoResumo {
  id: number
  nome: string
}

export interface Usuario {
  id: number
  nome: string
  username: string
  ativo: number
  grupos: GrupoResumo[]
}

export interface UsuarioLogado extends Usuario {
  permissoes: Permissao[]
}
