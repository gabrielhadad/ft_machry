import { PageHeading } from '../../components/ui'
import { TabelaDeMovimentacoes, useMovimentacoes } from '../../features/estoque'
import type { Mutacao } from '../../stores/dados'
import type { Lote, Produto } from '../../types'

interface MovimentacoesPageProps {
  lotes: Lote[]
  produtos: Produto[]
  atualizar: (mutacao: Mutacao) => Promise<boolean>
}

export function MovimentacoesPage({ lotes, produtos, atualizar }: MovimentacoesPageProps) {
  const historico = useMovimentacoes()

  const atualizarTudo = () => {
    void historico.atualizar()
    void atualizar('estoque')
  }

  return <>
    <PageHeading
      eyebrow="RASTREABILIDADE"
      title="Movimentações"
      description="Consulte entradas, saídas, ajustes, transferências e transformações. Navegue e filtre o histórico completo de movimentações."
      action={<button className="secondary" onClick={atualizarTudo} disabled={historico.carregando}>Atualizar</button>}
    />
    <TabelaDeMovimentacoes movimentos={historico.movimentos} lotes={lotes} produtos={produtos} erro={historico.erro} />
  </>
}
