import type { Localizacao, Produto } from '../../types'

export type Situacao = 'EM_DIA' | 'ATENCAO' | 'VENCIDO' | 'SEM_VALIDADE' | 'ESGOTADO'
export type FiltroSituacao = 'TODAS' | Situacao
export type Aba = 'ITENS' | 'MOVIMENTAR' | 'TRANSFERIR' | 'HISTORICO'
export type ModoItens = 'VER' | 'EDITAR' | 'ADICIONAR'
export type Operacao = 'TRANSFERENCIA' | 'TRANSFORMACAO'
export type TipoMovimento = 'ENTRADA' | 'SAIDA' | 'AJUSTE_ENTRADA' | 'AJUSTE_SAIDA'

export type Contexto = {
  produtosPorId: Map<number, Produto>
  locaisPorId: Map<number, Localizacao>
}

export type Grupo = {
  chave: number
  unidades: string
  conteudo: string
  fabricante: string
  fabricacao: string
  validade: string
  validadeManual: boolean
}

export interface NovoItem {
  quantidade_unidades: number
  quantidade: number
  fabricante: string | null
  data_fabricacao: string | null
  data_validade: string | null
}
