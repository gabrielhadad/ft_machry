import { useState, type FormEvent } from 'react'
import { SearchSelect } from '../../../components/ui'
import type { FaseCatalogo, FichaTecnica, Produto } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarFicha, criarFicha, type DadosDaFicha } from '../api/fichasApi'

type DraftPhase = { key: string; fase_id: number; ordem: number; tempo_previsto_min: number }
type DraftComponent = { key: string; produto_id: number; quantidade: number; fase_ordem: number | null }

let keySequence = 0
function novaChave() {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID()
  keySequence += 1
  return `${Date.now().toString(36)}-${keySequence.toString(36)}-${Math.random().toString(36).slice(2)}`
}

interface SheetEditorProps {
  ficha: FichaTecnica | null
  produtos: Produto[]
  catalogoFases: FaseCatalogo[]
  setSaving: (value: boolean) => void
  onSaved: () => void
}

export function SheetEditor({ ficha, produtos, catalogoFases, setSaving, onSaved }: SheetEditorProps) {
  const productsForSheet = produtos.filter((produto) => produto.tipo !== 'INSUMO')
  const componentOptions = produtos.map((produto) => ({ value: produto.id, label: `${produto.nome} (${produto.unidade_medida})` }))
  const [produtoId, setProdutoId] = useState(ficha?.produto_id ?? productsForSheet[0]?.id ?? 0)
  const [rendimento, setRendimento] = useState(ficha?.rendimento ?? 1)
  const [observacao, setObservacao] = useState(ficha?.observacao ?? '')
  const [fases, setFases] = useState<DraftPhase[]>(() => ficha
    ? ficha.fases.map((fase) => ({ key: novaChave(), fase_id: fase.fase_id, ordem: fase.ordem, tempo_previsto_min: fase.tempo_previsto_min }))
    : [{ key: novaChave(), fase_id: catalogoFases[0]?.id ?? 0, ordem: 1, tempo_previsto_min: 10 }])
  const [componentes, setComponentes] = useState<DraftComponent[]>(() => ficha
    ? ficha.componentes.map((item) => ({ key: novaChave(), produto_id: item.produto_id, quantidade: item.quantidade, fase_ordem: item.fase_ordem }))
    : [{ key: novaChave(), produto_id: produtos[0]?.id ?? 0, quantidade: 1, fase_ordem: 1 }])
  const [error, setError] = useState('')

  const updatePhase = (rowKey: string, change: Partial<DraftPhase>) =>
    setFases((rows) => rows.map((row) => row.key === rowKey ? { ...row, ...change } : row))
  const updateComponent = (rowKey: string, change: Partial<DraftComponent>) =>
    setComponentes((rows) => rows.map((row) => row.key === rowKey ? { ...row, ...change } : row))
  const addPhase = () =>
    setFases((rows) => [...rows, { key: novaChave(), fase_id: catalogoFases[0]?.id ?? 0, ordem: rows.length + 1, tempo_previsto_min: 10 }])
  const addComponent = () =>
    setComponentes((rows) => [...rows, { key: novaChave(), produto_id: produtos[0]?.id ?? 0, quantidade: 1, fase_ordem: fases[0]?.ordem ?? null }])
  const removePhase = (rowKey: string) => setFases((rows) => rows.filter((row) => row.key !== rowKey))
  const removeComponent = (rowKey: string) => setComponentes((rows) => rows.filter((row) => row.key !== rowKey))
  const etapaOptions = [{ value: '' as const, label: 'Sem vínculo' }, ...fases.map((fase) => ({ value: fase.ordem, label: `Etapa ${fase.ordem}` }))]

  async function save(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError('')
    const dados: DadosDaFicha = {
      produto_id: produtoId,
      rendimento,
      observacao: observacao.trim() || null,
      fases: fases.map(({ fase_id, ordem, tempo_previsto_min }) => ({ fase_id, ordem, tempo_previsto_min })),
      componentes: componentes.map(({ produto_id, quantidade, fase_ordem }) => ({ produto_id, quantidade, fase_ordem })),
    }
    try {
      if (ficha) await atualizarFicha(ficha.id, dados)
      else await criarFicha(dados)
      onSaved()
    } catch (reason) {
      setError(mensagemDeErro(reason, 'Não foi possível salvar a ficha.'))
    } finally {
      setSaving(false)
    }
  }

  return <form className="dialog-body sheet-editor" id="sheet-form" onSubmit={save}>
    {error && <p className="form-error">{error}</p>}
    {!productsForSheet.length && <p className="form-error">Cadastre um produto intermediário ou final antes de criar uma ficha.</p>}

    <div className="form-grid">
      <label>
        Produto produzido
        <SearchSelect
          required
          ariaLabel="Produto da ficha"
          placeholder="Buscar produto"
          value={produtoId}
          onChange={setProdutoId}
          options={productsForSheet.map((produto) => ({ value: produto.id, label: produto.nome }))}
        />
      </label>
      <label>
        Rendimento
        <input required type="number" min="0.001" step="0.001" value={rendimento} onChange={(event) => setRendimento(Number(event.target.value))} />
      </label>
    </div>

    <label>
      Observações
      <textarea rows={3} maxLength={2000} value={observacao} onChange={(event) => setObservacao(event.target.value)} />
    </label>

    <section className="subsection">
      <div>
        <h3>Etapas de preparo</h3>
        <button className="text-button" type="button" onClick={addPhase}>+ Adicionar etapa</button>
      </div>
      {fases.map((fase) => (
        <div className="form-row" key={fase.key}>
          <label>
            Ordem
            <input required type="number" min="1" value={fase.ordem} onChange={(event) => updatePhase(fase.key, { ordem: Number(event.target.value) })} />
          </label>
          <label>
            Fase
            <SearchSelect
              required
              ariaLabel="Fase"
              value={fase.fase_id}
              onChange={(faseId) => updatePhase(fase.key, { fase_id: faseId })}
              options={catalogoFases.map((item) => ({ value: item.id, label: item.nome }))}
            />
          </label>
          <label>
            Tempo (min)
            <input required type="number" min="1" value={fase.tempo_previsto_min} onChange={(event) => updatePhase(fase.key, { tempo_previsto_min: Number(event.target.value) })} />
          </label>
          <button className="remove-row" type="button" aria-label="Remover etapa" disabled={fases.length === 1} onClick={() => removePhase(fase.key)}>×</button>
        </div>
      ))}
    </section>

    <section className="subsection">
      <div>
        <h3>Componentes</h3>
        <button className="text-button" type="button" onClick={addComponent}>+ Adicionar componente</button>
      </div>
      {componentes.map((item) => (
        <div className="form-row component-row" key={item.key}>
          <label>
            Produto
            <SearchSelect
              required
              ariaLabel="Componente"
              placeholder="Buscar produto"
              value={item.produto_id}
              onChange={(produtoId) => updateComponent(item.key, { produto_id: produtoId })}
              options={componentOptions}
            />
          </label>
          <label>
            Quantidade
            <input required type="number" min="0.001" step="0.001" value={item.quantidade} onChange={(event) => updateComponent(item.key, { quantidade: Number(event.target.value) })} />
          </label>
          <label>
            Etapa
            <SearchSelect<number | ''>
              ariaLabel="Etapa"
              value={item.fase_ordem ?? ''}
              onChange={(ordem) => updateComponent(item.key, { fase_ordem: ordem === '' ? null : ordem })}
              options={etapaOptions}
            />
          </label>
          <button className="remove-row" type="button" aria-label="Remover componente" disabled={componentes.length === 1} onClick={() => removeComponent(item.key)}>×</button>
        </div>
      ))}
    </section>
  </form>
}
