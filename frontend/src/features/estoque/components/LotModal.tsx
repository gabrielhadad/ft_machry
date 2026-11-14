import { useState } from 'react'
import { EmptyState, Modal, SearchSelect } from '../../../components/ui'
import type { Lote, Produto } from '../../../types'
import { numero } from '../../../utils/formatacao'
import { tipoProdutoLabels } from '../../produtos'
import { useItensDoLote } from '../hooks/useItensDoLote'
import type { Aba, Contexto, ModoItens } from '../types'
import { itensAtivos, situacaoDo, temItens } from '../utils/lote'
import { AddItemsForm } from './AddItemsForm'
import { LotDetails } from './LotDetails'
import { LotEditForm } from './LotEditForm'
import { LotHistory } from './LotHistory'
import { MoveForm } from './MoveForm'
import { TransferForm } from './TransferForm'

function abasDoLote(lote: Lote): Array<[Aba, string]> {
  return [
    ['ITENS', temItens(lote) ? `Itens (${itensAtivos(lote)})` : 'Detalhes'],
    ['TRANSFERIR', 'Transferir ou transformar'],
    ['MOVIMENTAR', 'Movimentar'],
    ['HISTORICO', 'Histórico'],
  ]
}

interface LotModalProps {
  lote: Lote | null
  abaInicial: Aba
  lotes: Lote[]
  produtos: Produto[]
  contexto: Contexto
  usuarioId: number
  onClose: () => void
  onChanged: (mensagem: string) => Promise<void>
  onFinishedWithoutLot: () => void
}

export function LotModal({ lote, abaInicial, lotes, produtos, contexto, usuarioId, onClose, onChanged, onFinishedWithoutLot }: LotModalProps) {
  const [aba, setAba] = useState<Aba>(abaInicial)
  const [modo, setModo] = useState<ModoItens>('VER')
  const [origemId, setOrigemId] = useState<number | ''>(lote?.id ?? '')
  const [salvando, setSalvando] = useState(false)
  const origem = lote ?? lotes.find((item) => item.id === origemId) ?? null
  const produto = origem ? contexto.produtosPorId.get(origem.produto_id) : undefined
  const unidade = produto?.unidade_medida ?? ''
  const sit = origem ? situacaoDo(origem) : null
  const { itens, erro: erroItens, recarregar } = useItensDoLote(lote?.id ?? null, Boolean(lote && temItens(lote)))

  const trocarAba = (valor: Aba) => {
    setAba(valor)
    setModo('VER')
  }

  const concluir = async (mensagem: string) => {
    await onChanged(mensagem)
    recarregar()
    setModo('VER')
    if (lote) setAba('ITENS')
    else onFinishedWithoutLot()
  }

  let formId: string | undefined
  let textoSalvar = ''
  if (aba === 'MOVIMENTAR') { formId = 'move-form'; textoSalvar = 'Registrar movimento' }
  else if (aba === 'TRANSFERIR') { formId = 'transfer-form'; textoSalvar = 'Registrar operação' }
  else if (modo === 'EDITAR') { formId = 'lot-edit-form'; textoSalvar = 'Salvar lote' }
  else if (modo === 'ADICIONAR') { formId = 'add-items-form'; textoSalvar = 'Adicionar itens' }
  const podeAdicionarItens = lote !== null && (temItens(lote) || lote.quantidade === 0)

  function cancelar() {
    if (modo !== 'VER') setModo('VER')
    else if (lote && aba !== 'ITENS') trocarAba('ITENS')
    else onClose()
  }

  const footer = <>
    <button className="secondary outline" type="button" onClick={formId ? cancelar : onClose}>
      {formId ? 'Cancelar' : 'Fechar'}
    </button>
    <span className="dialog-actions-spacer" />
    {aba === 'ITENS' && modo === 'VER' && lote && <>
      <button className="secondary outline" type="button" onClick={() => setModo('EDITAR')}>Editar lote</button>
      <button
        className="primary"
        type="button"
        disabled={!podeAdicionarItens}
        title={podeAdicionarItens ? undefined : 'Este lote tem saldo sem itens. Zere o saldo (ajuste de saída) para passar a controlá-lo por itens.'}
        onClick={() => setModo('ADICIONAR')}
      >+ Adicionar itens</button>
    </>}
    {formId && <button className="primary" form={formId} type="submit" disabled={salvando || (aba === 'TRANSFERIR' && !origem)}>
      {salvando ? 'Salvando…' : textoSalvar}
    </button>}
  </>

  let subtitulo = 'Escolha o lote de origem e o destino da operação.'
  if (origem && temItens(origem)) {
    const disponiveis = `${origem.itens_disponiveis} ${origem.itens_disponiveis === 1 ? 'unidade disponível' : 'unidades disponíveis'}`
    subtitulo = `${origem.produto} · ${disponiveis} · ${numero.format(origem.quantidade)} ${unidade} em estoque`
  } else if (origem) {
    subtitulo = `${origem.produto} · ${numero.format(origem.quantidade)} ${unidade} em estoque`
  }

  const opcoesDeOrigem = [
    { value: '' as const, label: 'Selecione' },
    ...lotes.filter((item) => item.quantidade > 0).map((item) => ({
      value: item.id,
      label: `#${item.id} — ${item.produto} (${numero.format(item.quantidade)} ${contexto.produtosPorId.get(item.produto_id)?.unidade_medida ?? ''})`,
    })),
  ]

  return <Modal
    wide
    title={lote ? `Lote #${lote.id}` : 'Transferir ou transformar'}
    titleAside={lote && <>
      {produto && <span className={`badge ${produto.tipo.toLowerCase()}`}>{tipoProdutoLabels[produto.tipo]}</span>}
      {sit && <span className={`pill ${sit.tipo.toLowerCase()}`}>{sit.texto}</span>}
    </>}
    subtitle={subtitulo}
    onClose={onClose}
    footer={footer}
  >
    {lote && <nav className="modal-tabs" aria-label="Seções do lote">
      {abasDoLote(lote).map(([valor, label]) =>
        <button type="button" key={valor} className={aba === valor ? 'active' : ''} onClick={() => trocarAba(valor)}>{label}</button>)}
    </nav>}
    <div className="dialog-body lot-body">
      {aba === 'ITENS' && lote && modo === 'VER' && <LotDetails
        lote={lote}
        contexto={contexto}
        usuarioId={usuarioId}
        itens={itens}
        erroItens={erroItens}
        onItemChanged={concluir}
      />}
      {aba === 'ITENS' && lote && modo === 'EDITAR' && <LotEditForm
        lote={lote}
        produto={produto}
        contexto={contexto}
        onSaving={setSalvando}
        onSaved={() => concluir(`Lote #${lote.id} atualizado.`)}
      />}
      {aba === 'ITENS' && lote && modo === 'ADICIONAR' && <AddItemsForm
        lote={lote}
        unidade={unidade}
        validadeObrigatoria={Boolean(produto?.validade_obrigatoria)}
        validadePadraoDias={produto?.validade_padrao_dias}
        usuarioId={usuarioId}
        onSaving={setSalvando}
        onSaved={(quantidade) => concluir(`${quantidade} ${quantidade === 1 ? 'item adicionado' : 'itens adicionados'} ao lote #${lote.id}.`)}
      />}
      {aba === 'TRANSFERIR' && <>
        {!lote && <label className="field">
          Lote de origem
          <SearchSelect<number | ''> required ariaLabel="Lote de origem" placeholder="Buscar lote" value={origemId} onChange={setOrigemId} options={opcoesDeOrigem} />
        </label>}
        {origem
          ? <TransferForm key={origem.id} origem={origem} lotes={lotes} produtos={produtos} contexto={contexto} usuarioId={usuarioId} onSaving={setSalvando} onSaved={concluir} />
          : <EmptyState title="Selecione um lote" text="A operação parte de um lote com saldo disponível." />}
      </>}
      {aba === 'MOVIMENTAR' && lote && <MoveForm lote={lote} unidade={unidade} usuarioId={usuarioId} onSaving={setSalvando} onSaved={concluir} />}
      {aba === 'HISTORICO' && lote && <LotHistory lote={lote} />}
    </div>
  </Modal>
}
