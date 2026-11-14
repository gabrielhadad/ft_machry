import { PageHeading } from '../../components/ui'
import { TabelaDeMovimentacoes, useMovimentacoes } from '../../features/estoque'
import type { Lote, Produto } from '../../types'

interface MovimentacoesPageProps {
  lotes: Lote[]
  produtos: Produto[]
  rodadaDeAtualizacao: number
}

export function MovimentacoesPage({ lotes, produtos, rodadaDeAtualizacao }: MovimentacoesPageProps) {
  const historico = useMovimentacoes(rodadaDeAtualizacao)

  return <>
    <PageHeading
      eyebrow="RASTREABILIDADE"
      title="Movimentações"
      description="Consulte entradas, saídas, ajustes, transferências e transformações. Navegue e filtre o histórico completo de movimentações."
    />
    <TabelaDeMovimentacoes movimentos={historico.movimentos} lotes={lotes} produtos={produtos} erro={historico.erro} />
  </>
}
