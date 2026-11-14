import { useState } from 'react'
import { PageHeading } from '../../components/ui'
import { alterarStatusDaSolicitacao, criarSolicitacao, FilaDeProducao, MetricasDeProducao, PlanejadorDeProducao } from '../../features/producao'
import type { Mutacao } from '../../stores/dados'
import type { FichaTecnica, Localizacao, Produto, SolicitacaoProducao } from '../../types'
import { mensagemDeErro } from '../../utils/erros'

interface ProducaoPageProps {
  solicitacoes: SolicitacaoProducao[]
  fichas: FichaTecnica[]
  produtos: Produto[]
  localizacoes: Localizacao[]
  canPlan: boolean
  onViewSheet: (ficha: FichaTecnica) => void
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
  avisarErro: (mensagem: string) => void
}

export function ProducaoPage({ solicitacoes, fichas, produtos, localizacoes, canPlan, onViewSheet, aoAlterar, avisarErro }: ProducaoPageProps) {
  const [ocupado, setOcupado] = useState(false)

  const executar = async (acao: () => Promise<unknown>, erroPadrao: string, mensagemDeSucesso: string) => {
    setOcupado(true)
    try {
      await acao()
    } catch (reason) {
      avisarErro(mensagemDeErro(reason, erroPadrao))
      setOcupado(false)
      return
    }
    try {
      await aoAlterar('producao', mensagemDeSucesso)
    } finally {
      setOcupado(false)
    }
  }

  const criar = (fichaId: number, quantidade: number, localizacaoId: number) => executar(
    () => criarSolicitacao({ ficha_tecnica_id: fichaId, quantidade_planejada: quantidade, localizacao_destino_id: localizacaoId }),
    'Não foi possível adicionar o preparo.',
    'Preparo adicionado à fila.',
  )

  const alterarStatus = (id: number, status: string) => executar(
    () => alterarStatusDaSolicitacao(id, status),
    'Não foi possível atualizar o preparo.',
    status === 'CONCLUIDA' ? 'Preparo concluído.' : 'Preparo iniciado.',
  )

  return <>
    <PageHeading
      eyebrow="COZINHA"
      title="Produção"
      description="Fila de preparos definida pelo gestor para a equipe da cozinha."
      action={<button className="secondary no-print" onClick={() => window.print()}>Imprimir fila</button>}
    />
    <MetricasDeProducao solicitacoes={solicitacoes} />
    {canPlan && <PlanejadorDeProducao fichas={fichas} produtos={produtos} localizacoes={localizacoes} ocupado={ocupado} onCriar={criar} />}
    <FilaDeProducao solicitacoes={solicitacoes} fichas={fichas} ocupado={ocupado} onStatus={alterarStatus} onViewSheet={onViewSheet} />
  </>
}
