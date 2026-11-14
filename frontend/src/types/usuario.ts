export type PapelUsuario = 'OWNER' | 'ADMIN' | 'USER'

export interface Usuario {
  id: number
  nome: string
  username: string
  papel: PapelUsuario
  ativo: number
}
