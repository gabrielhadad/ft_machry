import { useState, type FormEvent } from 'react'
import { Modal, SearchSelect } from '../../../components/ui'
import type { Conservacao, Produto, TipoProduto } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarProduto, criarProduto, excluirProduto, type DadosDoProduto } from '../api/produtosApi'
import { opcoesDeConservacao, opcoesDeTipo } from '../rotulos'
import { unidadesMedida } from '../unidades'

interface ProductModalProps {
  produto: Produto | null
  onClose: () => void
  onSaved: () => void
  onDeleted: () => void
}

export function ProductModal({ produto, onClose, onSaved, onDeleted }: ProductModalProps) {
  const [nome, setNome] = useState(produto?.nome ?? '')
  const [tipo, setTipo] = useState<TipoProduto>(produto?.tipo ?? 'INSUMO')
  const [unidade, setUnidade] = useState(produto?.unidade_medida ?? 'kg')
  const [subdivisao, setSubdivisao] = useState(produto?.subdivisao ?? '')
  const [conservacao, setConservacao] = useState<Conservacao>(produto?.conservacao ?? 'SECO')
  const [validadeObrigatoria, setValidadeObrigatoria] = useState(Boolean(produto?.validade_obrigatoria))
  const [validadeDias, setValidadeDias] = useState(produto?.validade_padrao_dias?.toString() ?? '')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const unidadeAntiga = unidade && !unidadesMedida.some((item) => item.valor === unidade)
  const opcoesDeUnidade = [
    ...(unidadeAntiga ? [{ value: unidade, label: `${unidade} (cadastrada anteriormente)` }] : []),
    ...unidadesMedida.map((item) => ({ value: item.valor as string, label: item.nome })),
  ]

  async function save(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    const dados: DadosDoProduto = {
      nome: nome.trim(),
      tipo,
      unidade_medida: unidade,
      subdivisao: subdivisao.trim() || null,
      conservacao,
      validade_obrigatoria: validadeObrigatoria ? 1 : 0,
      validade_padrao_dias: validadeDias === '' ? null : Number(validadeDias),
    }
    try {
      if (produto) await atualizarProduto(produto.id, dados)
      else await criarProduto(dados)
      onSaved()
    } catch (reason) {
      setError(mensagemDeErro(reason, 'Não foi possível salvar o produto.'))
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (!produto || !window.confirm(`Excluir o produto “${produto.nome}”?`)) return
    setSaving(true)
    setError('')
    try {
      await excluirProduto(produto.id)
      onDeleted()
    } catch (reason) {
      setError(mensagemDeErro(reason, 'Não foi possível excluir o produto.'))
      setSaving(false)
    }
  }

  const footer = <>
    {produto && <button className="danger-link" onClick={remove} disabled={saving}>Excluir produto</button>}
    <button className="secondary" onClick={onClose} type="button">Cancelar</button>
    <button className="primary" form="product-form" disabled={saving}>{saving ? 'Salvando…' : 'Salvar produto'}</button>
  </>

  return <Modal eyebrow="CATÁLOGO" title={produto ? 'Editar produto' : 'Novo produto'} onClose={onClose} footer={footer}>
    <form className="dialog-body" id="product-form" onSubmit={save}>
      {error && <p className="form-error">{error}</p>}
      <label>
        Nome
        <input required maxLength={150} value={nome} onChange={(event) => setNome(event.target.value)} />
      </label>
      <div className="form-grid">
        <label>
          Tipo
          <SearchSelect ariaLabel="Tipo" value={tipo} onChange={setTipo} options={opcoesDeTipo} />
        </label>
        <label>
          Unidade de medida
          <SearchSelect required ariaLabel="Unidade de medida" value={unidade} onChange={setUnidade} options={opcoesDeUnidade} />
        </label>
        <label>
          Conservação
          <SearchSelect ariaLabel="Conservação" value={conservacao} onChange={setConservacao} options={opcoesDeConservacao} />
        </label>
        <label>
          Validade padrão (dias)
          <input type="number" min="0" value={validadeDias} onChange={(event) => setValidadeDias(event.target.value)} placeholder="Opcional" />
        </label>
      </div>
      <label>
        Subdivisão (opcional)
        <input maxLength={100} value={subdivisao} onChange={(event) => setSubdivisao(event.target.value)} placeholder="Ex.: sal fino, sal grosso, sal parrillero" />
        <small>Especifique a variação do produto para facilitar a busca e a organização.</small>
      </label>
      <label className="checkbox">
        <input type="checkbox" checked={validadeObrigatoria} onChange={(event) => setValidadeObrigatoria(event.target.checked)} /> Exigir data de validade nos lotes
      </label>
    </form>
  </Modal>
}
