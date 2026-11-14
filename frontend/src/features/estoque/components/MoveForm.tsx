import { useState, type FormEvent } from 'react'
import { RotuloDoCampo, SearchSelect } from '../../../components/ui'
import type { Lote } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { registrarMovimentacao } from '../api/estoqueApi'
import type { TipoMovimento } from '../types'
import { numeroDe } from '../utils/grupos'
import { situacaoDo, temItens } from '../utils/lote'

type OpcaoDeMovimento = { value: TipoMovimento; label: string }

const opcoesLoteVencido: OpcaoDeMovimento[] = [{ value: 'AJUSTE_SAIDA', label: 'Descarte / perda (ajuste de saída)' }]
const opcoesLoteComItens: OpcaoDeMovimento[] = [
  { value: 'SAIDA', label: 'Saída' },
  { value: 'AJUSTE_SAIDA', label: 'Ajuste de saída' },
]
const opcoesLoteSemItens: OpcaoDeMovimento[] = [
  { value: 'ENTRADA', label: 'Entrada' },
  { value: 'SAIDA', label: 'Saída' },
  { value: 'AJUSTE_ENTRADA', label: 'Ajuste de entrada' },
  { value: 'AJUSTE_SAIDA', label: 'Ajuste de saída' },
]

interface MoveFormProps {
  lote: Lote
  unidade: string
  usuarioId: number
  onSaving: (valor: boolean) => void
  onSaved: (mensagem: string) => Promise<void>
}

export function MoveForm({ lote, unidade, usuarioId, onSaving, onSaved }: MoveFormProps) {
  const porItens = temItens(lote)
  const vencido = situacaoDo(lote).tipo === 'VENCIDO'
  let opcoes = opcoesLoteSemItens
  if (vencido) opcoes = opcoesLoteVencido
  else if (porItens) opcoes = opcoesLoteComItens

  const [tipo, setTipo] = useState<TipoMovimento>(opcoes[0].value)
  const [quantidade, setQuantidade] = useState('')
  const [motivo, setMotivo] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')

  const pedeMotivo = tipo !== 'ENTRADA'
  const qtd = numeroDe(quantidade) || 0
  const somaNoLote = tipo === 'ENTRADA' || tipo === 'AJUSTE_ENTRADA'
  const saldoDepois = somaNoLote ? lote.quantidade + qtd : lote.quantidade - qtd

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setErro('')
    onSaving(true)
    try {
      await registrarMovimentacao({
        tipo,
        lote_id: lote.id,
        usuario_id: usuarioId,
        quantidade: qtd,
        motivo: motivo.trim() || null,
        observacao: observacao.trim() || null,
      })
      await onSaved('Movimento registrado.')
    } catch (reason) {
      setErro(mensagemDeErro(reason))
    } finally {
      onSaving(false)
    }
  }

  return <form id="move-form" className="lot-form" onSubmit={salvar}>
    {erro && <p className="form-error">{erro}</p>}
    {vencido && <p className="notice danger-notice">Este lote está vencido. Somente a baixa por perda ou descarte é permitida.</p>}
    {porItens && <p className="notice">
      Lote com itens: a saída consome primeiro os itens abertos e depois os que vencem antes.
      Para escolher os itens, use a aba “Transferir ou transformar” ou o botão “Consumir” na lista de itens.
    </p>}
    {vencido && <p className="notice">
      Lote vencido: só é permitida saída.{' '}
      {porItens && 'Itens vencidos saem pelo botão “Dar saída” na lista de itens; a saída por quantidade usa só os itens dentro da validade.'}
    </p>}
    <div className="form-grid">
      <label>
        Movimento
        <SearchSelect ariaLabel="Tipo de movimentação" value={tipo} onChange={setTipo} options={opcoes} />
      </label>
      <label>
        Quantidade ({unidade || 'unidade'})
        <input required type="number" min="0.001" step="any" value={quantidade} onChange={(event) => setQuantidade(event.target.value)} />
      </label>
    </div>
    {pedeMotivo && <label>
      Motivo
      <input required value={motivo} onChange={(event) => setMotivo(event.target.value)} placeholder="Ex.: uso na cozinha, perda ou correção" />
    </label>}
    <label>
      <RotuloDoCampo texto="Observação" opcional />
      <textarea rows={4} value={observacao} onChange={(event) => setObservacao(event.target.value)} />
    </label>
    <div className="transfer-summary">
      <div><span>Saldo atual</span><strong>{numero.format(lote.quantidade)} {unidade}</strong></div>
      <div><span>Movimento</span><strong>{qtd > 0 ? `${somaNoLote ? '+' : '−'}${numero.format(qtd)} ${unidade}` : '—'}</strong></div>
      <div><span>Saldo depois</span><strong>{numero.format(Math.max(0, saldoDepois))} {unidade}</strong></div>
    </div>
  </form>
}
