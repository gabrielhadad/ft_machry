import type { Conservacao, TipoProduto } from '../../types'

export const tipoProdutoLabels: Record<TipoProduto, string> = {
  INSUMO: 'Insumo',
  INTERMEDIARIO: 'Intermediário',
  FINAL: 'Produto final',
}

export const opcoesDeTipo = (Object.keys(tipoProdutoLabels) as TipoProduto[])
  .map((value) => ({ value, label: tipoProdutoLabels[value] }))

export const opcoesDeConservacao: { value: Conservacao; label: string }[] = [
  { value: 'SECO', label: 'Seco' },
  { value: 'RESFRIADO', label: 'Resfriado' },
  { value: 'CONGELADO', label: 'Congelado' },
]
