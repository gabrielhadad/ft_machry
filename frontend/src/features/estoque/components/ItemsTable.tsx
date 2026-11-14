import { useState } from 'react'
import type { ItemLote, StatusItem } from '../../../types'
import { formatarData } from '../../../utils/datas'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { abrirItem, registrarMovimentacao } from '../api/estoqueApi'
import { statusLabels } from '../rotulos'
import { destinoDoItem, itemVencido } from '../utils/lote'

type FiltroDeItens = StatusItem | 'VENCIDA' | 'TODOS'

const abasDeFiltro: Array<[FiltroDeItens, string]> = [
  ['TODOS', 'Todos'],
  ['DISPONIVEL', 'Disponíveis'],
  ['RESERVADA', 'Reservadas'],
  ['EM_USO', 'Em uso'],
  ['VENCIDA', 'Vencidas'],
  ['CONSUMIDA', 'Consumidas'],
]

interface ItemsTableProps {
  loteId: number
  usuarioId: number
  itens: ItemLote[] | null
  erro: string
  unidade: string
  onItemChanged: (mensagem: string) => Promise<void>
}

export function ItemsTable({ loteId, usuarioId, itens, erro, unidade, onItemChanged }: ItemsTableProps) {
  const [filtro, setFiltro] = useState<FiltroDeItens>('TODOS')
  const [itemEmAcao, setItemEmAcao] = useState<number | null>(null)
  const [erroAcao, setErroAcao] = useState('')

  async function executar(item: ItemLote, acao: () => Promise<unknown>, mensagem: string) {
    setItemEmAcao(item.id)
    setErroAcao('')
    try {
      await acao()
      await onItemChanged(mensagem)
    } catch (reason) {
      setErroAcao(mensagemDeErro(reason))
    } finally {
      setItemEmAcao(null)
    }
  }

  function abrir(item: ItemLote) {
    void executar(item, () => abrirItem(item.id), `${item.codigo} aberto.`)
  }

  function consumir(item: ItemLote) {
    const vencido = itemVencido(item)
    const registrar = () => registrarMovimentacao({
      tipo: vencido ? 'AJUSTE_SAIDA' : 'SAIDA',
      lote_id: loteId,
      usuario_id: usuarioId,
      item_ids: [item.id],
      motivo: vencido ? 'Descarte de item vencido' : 'Item consumido',
    })
    void executar(item, registrar, vencido ? `${item.codigo} descartado por vencimento.` : `${item.codigo} consumido.`)
  }

  if (erro) return <p className="form-error">{erro}</p>
  if (!itens) return <p className="helper">Carregando itens…</p>

  const visiveis = itens.filter((item) => {
    if (filtro === 'TODOS') return true
    if (filtro === 'VENCIDA') return itemVencido(item)
    return item.status === filtro && !itemVencido(item)
  })
  const ativos = itens.filter((item) => item.status !== 'CONSUMIDA' && !itemVencido(item)).length
  const algumEmAcao = itemEmAcao !== null

  return <div className="lot-section">
    <div className="lot-section-head">
      <h3>Itens do lote ({ativos})</h3>
      <div className="stock-tabs compact">
        {abasDeFiltro.map(([valor, label]) =>
          <button type="button" key={valor} className={filtro === valor ? 'active' : ''} onClick={() => setFiltro(valor)}>{label}</button>)}
      </div>
    </div>
    {erroAcao && <p className="form-error">{erroAcao}</p>}
    <div className="table-wrap items-table">
      <table>
        <thead>
          <tr><th>Código</th><th>Fabricante</th><th>Fabricação</th><th>Validade</th><th>Conteúdo</th><th>Status</th><th>Destino</th><th /></tr>
        </thead>
        <tbody>
          {visiveis.map((item) => {
            const vencido = itemVencido(item)
            const emAcao = itemEmAcao === item.id
            const parcialmenteUsado = item.saldo < item.quantidade && item.saldo > 0
            const podeAbrir = item.status === 'DISPONIVEL' && !vencido
            const podeConsumir = item.status === 'DISPONIVEL' || item.status === 'EM_USO'
            return <tr key={item.id}>
              <td><strong>{item.codigo}</strong></td>
              <td>{item.fabricante ?? '—'}</td>
              <td>{formatarData(item.data_fabricacao)}</td>
              <td><strong>{formatarData(item.data_validade)}</strong></td>
              <td>{parcialmenteUsado
                ? `${numero.format(item.saldo)} de ${numero.format(item.quantidade)} ${unidade}`
                : `${numero.format(item.quantidade)} ${unidade}`}</td>
              <td>{vencido
                ? <span className="pill vencido">Vencido</span>
                : <span className={`pill item-${item.status.toLowerCase()}`}>{statusLabels[item.status]}</span>}</td>
              <td>{destinoDoItem(item)}</td>
              <td>
                <div className="item-actions">
                  {emAcao && <span className="helper">Salvando…</span>}
                  {!emAcao && podeAbrir && <button type="button" className="text-button" disabled={algumEmAcao} onClick={() => abrir(item)}>Abrir</button>}
                  {!emAcao && podeConsumir && <button type="button" className="text-button" disabled={algumEmAcao} onClick={() => consumir(item)}>
                    {vencido ? 'Descartar' : 'Consumir'}
                  </button>}
                </div>
              </td>
            </tr>
          })}
        </tbody>
      </table>
    </div>
    {!visiveis.length && <p className="helper">Nenhum item com este status.</p>}
  </div>
}
