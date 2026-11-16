export type RecursoPermissao =
  | 'produtos'
  | 'fichas_tecnicas'
  | 'estoque'
  | 'localizacoes'
  | 'producao'
  | 'usuarios'
  | 'grupos_acesso'

export type AcaoPermissao = 'ler' | 'criar' | 'atualizar' | 'excluir'

export type Permissao = `${RecursoPermissao}:${AcaoPermissao}`

export interface PermissaoCatalogo {
  codigo: Permissao
  recurso: RecursoPermissao
  acao: AcaoPermissao
  descricao: string
}

export interface GrupoAcesso {
  id: number
  nome: string
  descricao: string | null
  protegido: number
  total_usuarios: number
  permissoes: PermissaoCatalogo[]
}
