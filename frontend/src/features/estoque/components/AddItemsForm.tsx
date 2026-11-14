import { useState, type FormEvent } from 'react'
import { RotuloDoCampo } from '../../../components/ui'
import type { Lote } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { adicionarItensAoLote } from '../api/estoqueApi'
import type { Grupo } from '../types'
import { grupoVazio, gruposParaApi, resumoDosGrupos } from '../utils/grupos'
import { GroupsEditor } from './GroupsEditor'

interface AddItemsFormProps {
  lote: Lote
  unidade: string
  validadeObrigatoria: boolean
  validadePadraoDias?: number | null
  usuarioId: number
  onSaving: (valor: boolean) => void
  onSaved: (quantidade: number) => Promise<void>
}

export function AddItemsForm({ lote, unidade, validadeObrigatoria, validadePadraoDias, usuarioId, onSaving, onSaved }: AddItemsFormProps) {
  const [grupos, setGrupos] = useState<Grupo[]>(() => [grupoVazio()])
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')
  const resumo = resumoDosGrupos(grupos)

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setErro('')
    onSaving(true)
    try {
      const criados = await adicionarItensAoLote(lote.id, {
        usuario_id: usuarioId,
        itens: gruposParaApi(grupos),
        observacao: observacao.trim() || null,
      })
      await onSaved(criados.length)
    } catch (reason) {
      setErro(mensagemDeErro(reason))
    } finally {
      onSaving(false)
    }
  }

  return <form id="add-items-form" className="lot-form" onSubmit={salvar}>
    {erro && <p className="form-error">{erro}</p>}
    <p className="helper">
      Cada unidade recebe um código próprio ({`FT-${String(lote.id).padStart(3, '0')}-…`}).
      {validadeObrigatoria && ' Grupos sem validade usam a validade do lote.'}
    </p>
    <GroupsEditor
      grupos={grupos}
      unidade={unidade}
      pedirValidade={validadeObrigatoria}
      validadeObrigatoria={validadeObrigatoria && !lote.data_validade}
      validadePadraoDias={validadePadraoDias}
      onChange={setGrupos}
    />
    <label>
      <RotuloDoCampo texto="Observação" opcional />
      <input value={observacao} onChange={(event) => setObservacao(event.target.value)} placeholder="Vai junto com a entrada" />
    </label>
    <div className="transfer-summary">
      <div><span>Unidades</span><strong>+{resumo.unidades}</strong></div>
      <div><span>Quantidade</span><strong>+{numero.format(resumo.quantidade)} {unidade}</strong></div>
      <div><span>Lote depois da entrada</span><strong>{numero.format(lote.quantidade + resumo.quantidade)} {unidade}</strong></div>
    </div>
  </form>
}
