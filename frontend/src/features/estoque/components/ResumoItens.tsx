import type { Lote } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { itensAtivos, temItens } from '../utils/lote'
import { BarraStatus } from './BarraStatus'

export function ResumoItens({ lote, unidade, vencido }: { lote: Lote; unidade: string; vencido: boolean }) {
  if (!temItens(lote)) {
    return <div className="item-summary">
      <span><strong>{numero.format(lote.quantidade)} {unidade}</strong> · sem itens</span>
    </div>
  }
  const disponiveis = `${lote.itens_disponiveis} ${lote.itens_disponiveis === 1 ? 'disponível' : 'disponíveis'}`
  const vencidas = lote.itens_vencidos > 0 ? ` · ${lote.itens_vencidos} ${lote.itens_vencidos === 1 ? 'vencida' : 'vencidas'}` : ''
  return <div className="item-summary">
    <span><strong>{itensAtivos(lote)} un</strong> · {disponiveis}{vencidas}</span>
    <BarraStatus lote={lote} vencido={vencido} />
  </div>
}
