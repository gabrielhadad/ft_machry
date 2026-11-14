import { useState } from 'react'
import { Modal } from '../../../components/ui'
import type { FaseCatalogo, FichaTecnica, Produto } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { excluirFicha } from '../api/fichasApi'
import { SheetDocument } from './SheetDocument'
import { SheetEditor } from './SheetEditor'

interface SheetModalProps {
  ficha: FichaTecnica | null
  produtos: Produto[]
  catalogoFases: FaseCatalogo[]
  canEdit: boolean
  onClose: () => void
  onSaved: () => void
  onDeleted: () => void
}

export function SheetModal({ ficha, produtos, catalogoFases, canEdit, onClose, onSaved, onDeleted }: SheetModalProps) {
  const [editing, setEditing] = useState(ficha === null)
  const [saving, setSaving] = useState(false)

  async function remove() {
    if (!ficha || !window.confirm(`Excluir a ficha de “${ficha.produto}”?`)) return
    setSaving(true)
    try {
      await excluirFicha(ficha.id)
      onDeleted()
    } catch (reason) {
      window.alert(mensagemDeErro(reason, 'Não foi possível excluir a ficha técnica.'))
    } finally {
      setSaving(false)
    }
  }

  function cancel() {
    if (editing && ficha) setEditing(false)
    else onClose()
  }

  function print() {
    if (!ficha || editing) return
    const cleanup = () => document.body.classList.remove('printing-sheet')
    document.body.classList.add('printing-sheet')
    window.addEventListener('afterprint', cleanup, { once: true })
    window.print()
    cleanup()
  }

  const footer = <>
    {ficha && canEdit && <button className="secondary outline" type="button" disabled={editing || saving} onClick={() => setEditing(true)}>Editar</button>}
    {editing && <button className="primary" form="sheet-form" disabled={saving}>{saving ? 'Salvando…' : 'Salvar'}</button>}
    <button className="secondary" onClick={cancel} type="button" disabled={saving}>Cancelar</button>
    {ficha && <button className="primary print-action" type="button" onClick={print} disabled={editing || saving}>Imprimir</button>}
    {ficha && canEdit && editing && <button className="danger-link" type="button" onClick={() => void remove()} disabled={saving}>Excluir ficha</button>}
  </>

  let title = 'Nova ficha técnica'
  if (ficha) title = editing ? 'Editar ficha técnica' : 'Ficha técnica'

  return <Modal className="sheet-dialog" eyebrow="PADRONIZAÇÃO" title={title} wide onClose={cancel} footer={footer}>
    {editing
      ? <SheetEditor key={`${ficha?.id ?? 'new'}-${editing}`} ficha={ficha} produtos={produtos} catalogoFases={catalogoFases} setSaving={setSaving} onSaved={onSaved} />
      : ficha && <SheetDocument ficha={ficha} />}
  </Modal>
}
