export interface CozinheiroResumo {
  id: number
  nome: string
  username: string
}

export interface Praca {
  id: number
  nome: string
  descricao: string | null
  ativo: number
  criado_em: string
  cozinheiros: CozinheiroResumo[]
}
