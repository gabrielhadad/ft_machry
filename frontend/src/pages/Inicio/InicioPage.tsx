import { Metric } from '../../components/ui'
import { FichasRecentes } from '../../features/fichas'
import type { FichaTecnica, Lote, Produto } from '../../types'

interface InicioPageProps {
  produtos: Produto[]
  fichas: FichaTecnica[]
  lotes: Lote[]
  canManage: boolean
  onNewSheet: () => void
  onViewSheet: (ficha: FichaTecnica) => void
}

export function InicioPage({ produtos, fichas, lotes, canManage, onNewSheet, onViewSheet }: InicioPageProps) {
  const lotesComSaldo = lotes.filter((lote) => lote.quantidade > 0)
  const unidadesCadastradas = lotesComSaldo.reduce((total, lote) => total + lote.itens_total - lote.itens_consumidos, 0)
  const detalheDosLotes = `em ${lotesComSaldo.length} ${lotesComSaldo.length === 1 ? 'lote ativo' : 'lotes ativos'}`

  return <>
    <section className="hero">
      <div>
        <span className="eyebrow">CENTRAL DE OPERAÇÕES</span>
        <h1>Sua cozinha, <em>sob controle.</em></h1>
        <p>Produtos, receitas, estoque e produção reunidos em uma visão simples para a rotina do estabelecimento.</p>
      </div>
      {canManage && <button className="primary" onClick={onNewSheet}>Nova ficha técnica</button>}
    </section>
    <section className="metrics">
      <Metric label="PRODUTOS ATIVOS" value={produtos.length} detail="itens cadastrados" />
      <Metric label="FICHAS TÉCNICAS" value={fichas.length} detail="receitas padronizadas" />
      <Metric label="UNIDADES CADASTRADAS" value={unidadesCadastradas} detail={detalheDosLotes} />
    </section>
    <FichasRecentes fichas={fichas} canManage={canManage} onNew={onNewSheet} onView={onViewSheet} />
  </>
}
