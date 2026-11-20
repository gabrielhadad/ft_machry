import { useState } from 'react'
import { PageHeading, SearchSelect } from '../../components/ui'
import {
  alterarPracaDaSolicitacao,
  alterarStatusDaSolicitacao,
  criarSolicitacao,
  FilaDeProducao,
  MetricasDeProducao,
  ModalDeAtribuicao,
  PlanejadorDeProducao,
} from '../../features/producao'
import type { Mutacao } from '../../stores/dados'
import type { FichaTecnica, Localizacao, Praca, Produto, SolicitacaoProducao } from '../../types'
import { mensagemDeErro } from '../../utils/erros'

interface ProducaoPageProps {
  solicitacoes: SolicitacaoProducao[]
  fichas: FichaTecnica[]
  produtos: Produto[]
  localizacoes: Localizacao[]
  pracas: Praca[]
  canPlan: boolean
  podeAtualizar: boolean
  podeConsultarPracas: boolean
  onViewSheet: (ficha: FichaTecnica) => void
  aoAlterar: (mutacao: Mutacao, mensagem: string) => Promise<void>
  avisarErro: (mensagem: string) => void
}

export function ProducaoPage({
  solicitacoes,
  fichas,
  produtos,
  localizacoes,
  pracas,
  canPlan,
  podeAtualizar,
  podeConsultarPracas,
  onViewSheet,
  aoAlterar,
  avisarErro,
}: ProducaoPageProps) {
  const [ocupado, setOcupado] = useState(false)
  const [filtroPraca, setFiltroPraca] = useState(0)
  const [reatribuindo, setReatribuindo] = useState<SolicitacaoProducao | null>(null)
  const pracasDisponiveis = podeConsultarPracas ? pracas : []
  const nomesDePracas = new Map(pracas.map((praca) => [praca.id, praca.nome]))
  solicitacoes.forEach((solicitacao) => {
    if (solicitacao.praca) nomesDePracas.set(solicitacao.praca.id, solicitacao.praca.nome)
  })
  const solicitacoesFiltradas = solicitacoes.filter((item) => {
    if (filtroPraca === 0) return true
    if (filtroPraca === -1) return item.praca_id === null
    return item.praca_id === filtroPraca
  })

  const executar = async (
    acao: () => Promise<unknown>,
    erroPadrao: string,
    mensagemDeSucesso: string,
  ) => {
    setOcupado(true)
    try {
      await acao()
      await aoAlterar('producao', mensagemDeSucesso)
    } catch (reason) {
      avisarErro(mensagemDeErro(reason, erroPadrao))
    } finally {
      setOcupado(false)
    }
  }

  const criar = (fichaId: number, quantidade: number, localizacaoId: number, pracaId: number | null) => executar(
    () => criarSolicitacao({
      ficha_tecnica_id: fichaId,
      quantidade_planejada: quantidade,
      localizacao_destino_id: localizacaoId,
      praca_id: pracaId,
    }),
    'Não foi possível adicionar o preparo.',
    'Preparo adicionado à fila.',
  )

  const alterarStatus = (id: number, status: string) => executar(
    () => alterarStatusDaSolicitacao(id, status),
    'Não foi possível atualizar o preparo.',
    status === 'CONCLUIDA' ? 'Preparo concluído.' : 'Preparo iniciado.',
  )

  const salvarAtribuicao = async (id: number, pracaId: number | null) => {
    setOcupado(true)
    try {
      await alterarPracaDaSolicitacao(id, pracaId)
      await aoAlterar('producao', 'Praça da solicitação atualizada.')
    } finally {
      setOcupado(false)
    }
  }

  const acaoDeImprimir = <button className="secondary no-print" onClick={() => window.print()}>
    Imprimir fila
  </button>

  return <>
    <PageHeading
      eyebrow="COZINHA"
      title="Produção"
      description="Fila de preparos definida pelo gestor para a equipe da cozinha."
      action={acaoDeImprimir}
    />
    {canPlan && <MetricasDeProducao solicitacoes={solicitacoes} />}
    {canPlan && <PlanejadorDeProducao
      fichas={fichas}
      produtos={produtos}
      localizacoes={localizacoes}
      pracas={pracasDisponiveis}
      ocupado={ocupado}
      onCriar={criar}
    />}
    <section className="production-filters no-print" aria-label="Filtros da produção">
      <label>
        Filtrar por praça
        <SearchSelect
          ariaLabel="Filtrar solicitações por praça"
          value={filtroPraca}
          onChange={setFiltroPraca}
          options={[
            { value: 0, label: 'Todas as praças' },
            { value: -1, label: 'Sem praça' },
            ...Array.from(nomesDePracas, ([id, nome]) => ({ value: id, label: nome }))
              .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR')),
          ]}
        />
      </label>
      <span>{solicitacoesFiltradas.length} de {solicitacoes.length} solicitações</span>
    </section>
    <FilaDeProducao
      solicitacoes={solicitacoesFiltradas}
      fichas={fichas}
      ocupado={ocupado}
      podeAtualizar={podeAtualizar}
      podeAtribuir={canPlan && podeConsultarPracas}
      onAtribuir={setReatribuindo}
      onStatus={alterarStatus}
      onViewSheet={onViewSheet}
    />
    {reatribuindo && <ModalDeAtribuicao
      solicitacao={reatribuindo}
      pracas={pracasDisponiveis}
      onSalvar={salvarAtribuicao}
      onClose={() => setReatribuindo(null)}
    />}
  </>
}
