import { useState, type FormEvent } from 'react'
import { Modal, MoneyInput, RotuloDoCampo, SearchSelect } from '../../../components/ui'
import type { Localizacao, Produto } from '../../../types'
import { formatarData, hojeIso } from '../../../utils/datas'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { tipoProdutoLabels } from '../../produtos'
import { criarLote } from '../api/estoqueApi'
import type { Grupo } from '../types'
import { grupoVazio, gruposParaApi, resumoDosGrupos, sugerirValidade, sugerirValidadeDosGrupos } from '../utils/grupos'
import { GroupsEditor } from './GroupsEditor'

const temValidade = (produto?: Produto) => Boolean(produto?.validade_obrigatoria) || produto?.validade_padrao_dias != null

interface NewLotModalProps {
  produtos: Produto[]
  localizacoes: Localizacao[]
  usuarioId: number
  onClose: () => void
  onSaved: (loteId: number) => Promise<void>
}

export function NewLotModal({ produtos, localizacoes, usuarioId, onClose, onSaved }: NewLotModalProps) {
  const [produtoId, setProdutoId] = useState<number | ''>('')
  const [localizacaoId, setLocalizacaoId] = useState<number | ''>('')
  const [entrada, setEntrada] = useState(hojeIso())
  const [validadeLote, setValidadeLote] = useState('')
  const [validadeLoteManual, setValidadeLoteManual] = useState(false)
  const [fornecedor, setFornecedor] = useState('')
  const [notaFiscal, setNotaFiscal] = useState('')
  const [custo, setCusto] = useState('')
  const [grupos, setGrupos] = useState<Grupo[]>(() => [grupoVazio()])
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')
  const [salvando, setSalvando] = useState(false)

  const produto = produtos.find((item) => item.id === produtoId)
  const unidade = produto?.unidade_medida ?? ''
  const locaisCompativeis = localizacoes.filter((item) => !produto || item.tipo === produto.conservacao)
  const resumo = resumoDosGrupos(grupos)
  const vencimento = resumo.menorValidade || validadeLote
  const pedirValidade = temValidade(produto)
  const diasPadrao = produto?.validade_padrao_dias

  function trocarProduto(id: number | '') {
    setProdutoId(id)
    const escolhido = produtos.find((item) => item.id === id)
    setLocalizacaoId(localizacoes.find((item) => item.tipo === escolhido?.conservacao)?.id ?? '')
    setValidadeLoteManual(false)
    if (!temValidade(escolhido)) {
      setValidadeLote('')
      setGrupos((atuais) => atuais.map((grupo) => ({ ...grupo, validade: '', validadeManual: false })))
      return
    }
    setValidadeLote(sugerirValidade(entrada, escolhido?.validade_padrao_dias))
    setGrupos((atuais) => sugerirValidadeDosGrupos(atuais.map((grupo) => ({ ...grupo, validadeManual: false })), escolhido?.validade_padrao_dias))
  }

  function trocarEntrada(valor: string) {
    setEntrada(valor)
    if (pedirValidade && !validadeLoteManual) setValidadeLote(sugerirValidade(valor, diasPadrao))
  }

  async function salvar(event: FormEvent) {
    event.preventDefault()
    if (!produtoId || !localizacaoId) {
      setErro('Escolha o produto e a localização.')
      return
    }
    setErro('')
    setSalvando(true)
    try {
      const lote = await criarLote({
        produto_id: produtoId,
        localizacao_id: localizacaoId,
        data_producao: entrada || null,
        data_validade: validadeLote || null,
        custo_unitario: custo === '' ? null : Number(custo),
        fornecedor: fornecedor.trim() || null,
        nota_fiscal: notaFiscal.trim() || null,
        itens: gruposParaApi(grupos),
        usuario_id: usuarioId,
        observacao: observacao.trim() || null,
      })
      await onSaved(lote.id)
    } catch (reason) {
      setErro(mensagemDeErro(reason))
    } finally {
      setSalvando(false)
    }
  }

  const footer = <>
    <button className="secondary outline" type="button" onClick={onClose}>Cancelar</button>
    <span className="dialog-actions-spacer" />
    <button className="primary" form="new-lot-form" type="submit" disabled={salvando}>{salvando ? 'Salvando…' : 'Salvar lote'}</button>
  </>

  return <Modal wide eyebrow="ESTOQUE" title="Novo lote" subtitle="Registre a entrada e as unidades que chegaram; cada unidade recebe um código próprio." onClose={onClose} footer={footer}>
    <form id="new-lot-form" className="dialog-body lot-body new-lot" onSubmit={salvar}>
      {erro && <p className="form-error">{erro}</p>}

      <section className="lot-section">
        <h3>Dados do lote</h3>
        <div className="form-grid">
          <label>
            Produto
            <SearchSelect<number | ''>
              required
              ariaLabel="Produto"
              placeholder="Buscar produto"
              value={produtoId}
              onChange={trocarProduto}
              options={[{ value: '', label: 'Selecione' }, ...produtos.map((item) => ({ value: item.id, label: `${item.nome} · ${tipoProdutoLabels[item.tipo]}` }))]}
            />
          </label>
          <label>
            Localização
            <SearchSelect<number | ''>
              required
              ariaLabel="Localização"
              disabled={!produto}
              placeholder={produto ? 'Buscar localização' : 'Escolha o produto'}
              value={localizacaoId}
              onChange={setLocalizacaoId}
              options={[{ value: '', label: 'Selecione' }, ...locaisCompativeis.map((item) => ({ value: item.id, label: item.nome }))]}
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
            Tipo
            <input value={produto ? tipoProdutoLabels[produto.tipo] : ''} placeholder="Definido pelo produto" disabled />
          </label>
          <label>
            Data de entrada
            <input type="date" value={entrada} onChange={(event) => trocarEntrada(event.target.value)} />
          </label>
          {pedirValidade && <label>
            <RotuloDoCampo texto="Validade do lote" opcional />
            <input type="date" value={validadeLote} onChange={(event) => { setValidadeLote(event.target.value); setValidadeLoteManual(true) }} />
          </label>}
        </div>
        {pedirValidade && diasPadrao != null && <p className="helper">
          Validade sugerida pela validade padrão do produto ({diasPadrao} {diasPadrao === 1 ? 'dia' : 'dias'} a partir da entrada ou da fabricação do grupo). Pode ser alterada.
        </p>}
      </section>

      <section className="lot-section">
        <h3>Itens do lote</h3>
        <GroupsEditor
          grupos={grupos}
          unidade={unidade}
          pedirValidade={pedirValidade}
          validadeObrigatoria={Boolean(produto?.validade_obrigatoria) && !validadeLote}
          validadePadraoDias={diasPadrao}
          onChange={setGrupos}
        />
        {pedirValidade && <p className="helper">O vencimento do lote passa a ser a validade mais próxima entre as unidades. Grupos sem validade usam a validade do lote.</p>}
        <label>
          <RotuloDoCampo texto="Observação" opcional />
          <textarea rows={3} value={observacao} onChange={(event) => setObservacao(event.target.value)} />
        </label>
      </section>

      <div className="transfer-summary four">
        <div><span>Unidades</span><strong>{resumo.unidades}</strong></div>
        <div><span>Quantidade total</span><strong>{numero.format(resumo.quantidade)} {unidade}</strong></div>
        <div><span>Entrada</span><strong>{formatarData(entrada || null)}</strong></div>
        <div><span>Vencimento</span><strong>{produto && !pedirValidade ? 'Sem validade' : formatarData(vencimento || null)}</strong></div>
      </div>
    </form>
  </Modal>
}
