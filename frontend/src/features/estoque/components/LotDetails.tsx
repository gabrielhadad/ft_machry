import type { ItemLote, Lote } from '../../../types'
import { formatarData } from '../../../utils/datas'
import type { Contexto } from '../types'
import { caminhoLocalizacao, dataEntrada, situacaoDo, temItens, vidaUtil } from '../utils/lote'
import { BarraStatus } from './BarraStatus'
import { ItemsTable } from './ItemsTable'

interface LotDetailsProps {
  lote: Lote
  contexto: Contexto
  usuarioId: number
  itens: ItemLote[] | null
  erroItens: string
  onItemChanged: (mensagem: string) => Promise<void>
}

export function LotDetails({ lote, contexto, usuarioId, itens, erroItens, onItemChanged }: LotDetailsProps) {
  const produto = contexto.produtosPorId.get(lote.produto_id)
  const unidade = produto?.unidade_medida ?? ''
  const sit = situacaoDo(lote)
  const vida = vidaUtil(lote)
  const vidaDecorrida = vida && <small>{vida.decorridos} de {vida.total} dias de vida útil decorridos</small>

  return <>
    <div className="info-grid">
      <div><span>ENTRADA</span><strong>{formatarData(dataEntrada(lote))}</strong></div>
      <div><span>VENCIMENTO</span><strong>{formatarData(lote.data_validade)}</strong></div>
      <div><span>LOCALIZAÇÃO</span><strong>{caminhoLocalizacao(lote.localizacao_id, contexto.locaisPorId, lote.localizacao)}</strong></div>
      <div><span>FORNECEDOR</span><strong>{lote.fornecedor ?? '—'}</strong></div>
    </div>

    {temItens(lote)
      ? <>
        <div className="lot-section">
          <div className="lot-section-head">
            <h3>Situação dos itens</h3>
            {vidaDecorrida}
          </div>
          <BarraStatus lote={lote} />
          <div className="status-counts">
            <span><i className="disponivel" /><strong>{lote.itens_disponiveis}</strong> disponíveis</span>
            <span><i className="reservada" /><strong>{lote.itens_reservados}</strong> reservadas</span>
            <span><i className="em_uso" /><strong>{lote.itens_em_uso}</strong> em uso</span>
            <span><i className="vencido" /><strong>{lote.itens_vencidos}</strong> vencidas</span>
            <span><i className="consumida" /><strong>{lote.itens_consumidos}</strong> consumidas</span>
          </div>
        </div>
        <ItemsTable loteId={lote.id} usuarioId={usuarioId} itens={itens} erro={erroItens} unidade={unidade} onItemChanged={onItemChanged} />
      </>
      : <>
        <div className="lot-section">
          <div className="lot-section-head">
            <h3>Vida útil</h3>
            {vidaDecorrida}
          </div>
          {vida
            ? <div className={`life-bar ${sit.tipo.toLowerCase()}`}><i style={{ width: `${(vida.decorridos / vida.total) * 100}%` }} /></div>
            : <p className="helper">Lote sem data de validade cadastrada.</p>}
        </div>
        <p className="notice">
          Este lote é controlado só pela quantidade total, sem itens individuais.{' '}
          {lote.quantidade === 0
            ? 'Como está sem saldo, você pode passar a controlá-lo por itens com “+ Adicionar itens”.'
            : 'Para cadastrar itens, primeiro zere o saldo com “Movimentar” → ajuste de saída, ou crie um novo lote já com os itens.'}
        </p>
      </>}
  </>
}
