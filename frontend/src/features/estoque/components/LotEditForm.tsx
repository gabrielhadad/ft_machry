import { useState, type FormEvent } from 'react'
import { MoneyInput, RotuloDoCampo, SearchSelect } from '../../../components/ui'
import type { Lote, Produto } from '../../../types'
import { mensagemDeErro } from '../../../utils/erros'
import { atualizarLote, type AlteracaoDoLote } from '../api/estoqueApi'
import type { Contexto } from '../types'
import { caminhoLocalizacao, temItens } from '../utils/lote'

interface LotEditFormProps {
  lote: Lote
  produto: Produto | undefined
  contexto: Contexto
  onSaving: (valor: boolean) => void
  onSaved: () => Promise<void>
}

export function LotEditForm({ lote, produto, contexto, onSaving, onSaved }: LotEditFormProps) {
  const [localizacaoId, setLocalizacaoId] = useState(lote.localizacao_id)
  const [entrada, setEntrada] = useState(lote.data_producao ?? '')
  const [validade, setValidade] = useState(lote.data_validade ?? '')
  const [custo, setCusto] = useState(lote.custo_unitario === null ? '' : lote.custo_unitario.toFixed(2))
  const [fornecedor, setFornecedor] = useState(lote.fornecedor ?? '')
  const [notaFiscal, setNotaFiscal] = useState(lote.nota_fiscal ?? '')
  const [erro, setErro] = useState('')
  const controladoPorItens = temItens(lote)

  async function salvar(event: FormEvent) {
    event.preventDefault()
    setErro('')
    onSaving(true)
    const alteracao: AlteracaoDoLote = {
      localizacao_id: localizacaoId,
      data_producao: entrada || null,
      custo_unitario: custo === '' ? null : Number(custo),
      fornecedor: fornecedor.trim() || null,
      nota_fiscal: notaFiscal.trim() || null,
    }
    if (!controladoPorItens) alteracao.data_validade = validade || null
    try {
      await atualizarLote(lote.id, alteracao)
      await onSaved()
    } catch (reason) {
      setErro(mensagemDeErro(reason))
    } finally {
      onSaving(false)
    }
  }

  const locaisCompativeis = [...contexto.locaisPorId.values()].filter((local) => !produto || local.tipo === produto.conservacao)

  return <form id="lot-edit-form" className="lot-form" onSubmit={salvar}>
    {erro && <p className="form-error">{erro}</p>}
    <div className="form-grid">
      <label>
        Localização
        <SearchSelect
          required
          ariaLabel="Localização"
          placeholder="Buscar localização"
          value={localizacaoId}
          onChange={setLocalizacaoId}
          options={locaisCompativeis.map((local) => ({ value: local.id, label: caminhoLocalizacao(local.id, contexto.locaisPorId, local.nome) }))}
        />
      </label>
      <label>
        <RotuloDoCampo texto="Fornecedor" opcional />
        <input maxLength={150} value={fornecedor} onChange={(event) => setFornecedor(event.target.value)} />
      </label>
      <label>
        <RotuloDoCampo texto="Nota fiscal" opcional />
        <input maxLength={60} value={notaFiscal} onChange={(event) => setNotaFiscal(event.target.value)} />
      </label>
      <label>
        <RotuloDoCampo texto="Custo unitário" opcional />
        <MoneyInput value={custo} onChange={setCusto} placeholder="R$ 0,00" />
      </label>
      <label>
        Data de entrada
        <input type="date" value={entrada} onChange={(event) => setEntrada(event.target.value)} />
      </label>
      <label>
        Validade
        <input type="date" value={validade} disabled={controladoPorItens} onChange={(event) => setValidade(event.target.value)} />
      </label>
    </div>
    {controladoPorItens && <p className="helper">Em lotes com itens, o vencimento é a validade mais próxima entre os itens; edite a validade de cada item.</p>}
  </form>
}
