import type { Lote } from '../../../types'

export function BarraStatus({ lote, vencido }: { lote: Lote; vencido?: boolean }) {
  if (vencido) {
    return <div className="status-bar"><i className="vencido" style={{ flex: 1 }} /></div>
  }
  const partes: Array<[string, number]> = [
    ['disponivel', lote.itens_disponiveis],
    ['reservada', lote.itens_reservados],
    ['em_uso', lote.itens_em_uso],
    ['vencido', lote.itens_vencidos],
    ['consumida', lote.itens_consumidos],
  ]
  return <div className="status-bar">
    {partes
      .filter(([, quantidade]) => quantidade > 0)
      .map(([classe, quantidade]) => <i key={classe} className={classe} style={{ flex: quantidade }} />)}
  </div>
}
