import { useState, type FormEvent } from 'react'
import { RotuloDoCampo, SearchSelect } from '../../../components/ui'
import type { Lote, Produto } from '../../../types'
import { formatarDiaMes } from '../../../utils/datas'
import { mensagemDeErro } from '../../../utils/erros'
import { numero } from '../../../utils/formatacao'
import { tipoProdutoLabels } from '../../produtos'
import { registrarMovimentacao } from '../api/estoqueApi'
import { useItensDoLote } from '../hooks/useItensDoLote'
import type { Contexto, Operacao } from '../types'
import { numeroDe } from '../utils/grupos'
import { caminhoLocalizacao, itemVencido, ordemDeUso, temItens } from '../utils/lote'

interface TransferFormProps {
  origem: Lote
  lotes: Lote[]
  produtos: Produto[]
  contexto: Contexto
  usuarioId: number
  onSaving: (valor: boolean) => void
  onSaved: (mensagem: string) => Promise<void>
}

export function TransferForm({ origem, lotes, produtos, contexto, usuarioId, onSaving, onSaved }: TransferFormProps) {
  const [operacao, setOperacao] = useState<Operacao>('TRANSFERENCIA')
  const [quantidade, setQuantidade] = useState('')
  const [selecionados, setSelecionados] = useState<number[]>([])
  const [produtoDestinoId, setProdutoDestinoId] = useState<number | ''>('')
  const [destinoId, setDestinoId] = useState<number | ''>('')
  const [localizacaoDestinoId, setLocalizacaoDestinoId] = useState<number | ''>('')
  const [rendimento, setRendimento] = useState('')
  const [observacao, setObservacao] = useState('')
  const [erro, setErro] = useState('')

  const porItens = temItens(origem)
  const transformacao = operacao === 'TRANSFORMACAO'
  const { itens } = useItensDoLote(origem.id, porItens)
  const livres = (itens ?? [])
    .filter((item) => (item.status === 'DISPONIVEL' || item.status === 'EM_USO') && !itemVencido(item))
    .sort(ordemDeUso)
  const escolhidos = livres.filter((item) => selecionados.includes(item.id))

  const produtoOrigem = contexto.produtosPorId.get(origem.produto_id)
  const unidadeOrigem = produtoOrigem?.unidade_medida ?? ''
  let produtoDestino = produtoOrigem
  if (transformacao) produtoDestino = produtoDestinoId === '' ? undefined : contexto.produtosPorId.get(produtoDestinoId)
  const unidadeDestino = produtoDestino?.unidade_medida ?? ''

  const lotesDestino = lotes.filter((lote) => {
    if (lote.id === origem.id || !produtoDestino || lote.produto_id !== produtoDestino.id) return false
    if (transformacao) return true
    return porItens ? temItens(lote) || lote.quantidade === 0 : !temItens(lote)
  })
  const loteDestino = lotes.find((lote) => lote.id === destinoId)
  const localizacoesDestino = [...contexto.locaisPorId.values()].filter(
    (local) => local.id !== origem.localizacao_id && local.tipo === produtoOrigem?.conservacao,
  )
  const localizacaoDestino = localizacaoDestinoId === '' ? undefined : contexto.locaisPorId.get(localizacaoDestinoId)
  const opcoesDeProdutoResultante = [
    { value: '' as const, label: 'Selecione' },
    ...produtos
      .filter((item) => item.id !== origem.produto_id)
      .map((item) => ({ value: item.id, label: `${item.nome} (${tipoProdutoLabels[item.tipo].toLowerCase()})` })),
  ]

  const qtd = porItens ? escolhidos.reduce((total, item) => total + item.saldo, 0) : numeroDe(quantidade)
  const qtdDestino = transformacao ? numeroDe(rendimento) : qtd
  const qtdValida = qtd > 0 && qtd <= origem.quantidade
  const fator = qtd > 0 && qtdDestino > 0 ? qtdDestino / qtd : null
  const disponiveisDepois = origem.itens_disponiveis - escolhidos.filter((item) => item.status === 'DISPONIVEL').length

  const trocarOperacao = (valor: Operacao) => {
    setOperacao(valor)
    setDestinoId('')
    setLocalizacaoDestinoId('')
    setProdutoDestinoId('')
    setRendimento('')
  }
  const alternar = (id: number) =>
    setSelecionados((atual) => atual.includes(id) ? atual.filter((valor) => valor !== id) : [...atual, id])
  const usarPrimeiros = (quantos: number) =>
    setSelecionados(livres.slice(0, Math.max(0, quantos)).map((item) => item.id))

  function validar() {
    if (porItens && !escolhidos.length) return 'Selecione os itens a usar.'
    if (!qtdValida) return `Informe uma quantidade entre 0 e ${numero.format(origem.quantidade)} ${unidadeOrigem}.`
    if (!transformacao && !localizacaoDestino) return 'Selecione a localização de destino.'
    if (transformacao && !loteDestino) return 'Selecione o lote de destino.'
    if (transformacao && !(qtdDestino > 0)) return 'Informe o rendimento da transformação.'
    return ''
  }

  async function salvar(event: FormEvent) {
    event.preventDefault()
    const problema = validar()
    setErro(problema)
    if (problema) return
    onSaving(true)
    try {
      await registrarMovimentacao({
        tipo: operacao,
        lote_id: origem.id,
        lote_destino_id: transformacao ? loteDestino?.id : null,
        localizacao_destino_id: transformacao ? null : localizacaoDestino?.id,
        usuario_id: usuarioId,
        quantidade: porItens ? null : qtd,
        item_ids: porItens ? escolhidos.map((item) => item.id) : null,
        quantidade_destino: transformacao ? qtdDestino : null,
        observacao: observacao.trim() || null,
      })
      await onSaved(transformacao ? 'Transformação registrada.' : 'Transferência registrada.')
    } catch (reason) {
      setErro(mensagemDeErro(reason))
    } finally {
      onSaving(false)
    }
  }

  const resumoDaOrigem = porItens
    ? `${origem.itens_disponiveis} → ${disponiveisDepois} unidades disponíveis`
    : `${numero.format(origem.quantidade)} → ${numero.format(qtdValida ? origem.quantidade - qtd : origem.quantidade)} ${unidadeOrigem}`
  const destinoRecebe = qtdDestino > 0 && produtoDestino ? `+${numero.format(qtdDestino)} ${unidadeDestino} de ${produtoDestino.nome}` : '—'
  let resumoFinal = localizacaoDestino ? caminhoLocalizacao(localizacaoDestino.id, contexto.locaisPorId, localizacaoDestino.nome) : '—'
  if (transformacao) resumoFinal = fator ? `${numero.format(fator)} ${unidadeDestino} por ${unidadeOrigem}` : '—'

  return <form id="transfer-form" className="transfer-form" onSubmit={salvar}>
    {erro && <p className="form-error">{erro}</p>}
    <fieldset className="operation-cards">
      <legend>Operação</legend>
      <label className={operacao === 'TRANSFERENCIA' ? 'active' : ''}>
        <input type="radio" name="operacao" checked={operacao === 'TRANSFERENCIA'} onChange={() => trocarOperacao('TRANSFERENCIA')} />
        <span><strong>Transferência</strong><small>Move o mesmo produto para outro lote ou local.</small></span>
      </label>
      <label className={transformacao ? 'active' : ''}>
        <input type="radio" name="operacao" checked={transformacao} onChange={() => trocarOperacao('TRANSFORMACAO')} />
        <span><strong>Transformação</strong><small>Converte itens deste lote em outro produto, com rendimento informado.</small></span>
      </label>
    </fieldset>

    <div className="transfer-grid">
      <section className="transfer-card">
        <div className="transfer-card-head"><h3>Origem · lote #{origem.id}</h3><small>{origem.produto}</small></div>
        {porItens
          ? <>
            <span className="field-label">Itens a usar (selecione as unidades)</span>
            {itens === null && <p className="helper">Carregando itens…</p>}
            <div className="item-picker">
              {livres.map((item) => <label key={item.id} className={selecionados.includes(item.id) ? 'checked' : ''}>
                <input type="checkbox" checked={selecionados.includes(item.id)} onChange={() => alternar(item.id)} />
                <strong>{item.codigo}</strong>
                <small>{numero.format(item.saldo)} {unidadeOrigem}{item.status === 'EM_USO' ? ' · aberta' : ''} · vence {formatarDiaMes(item.data_validade)}</small>
              </label>)}
              {itens !== null && !livres.length && <p className="helper">Nenhum item disponível neste lote.</p>}
            </div>
            <div className="transfer-total">
              <label className="inline-number">
                Usar as que vencem primeiro
                <input type="number" min="0" max={livres.length} value={escolhidos.length} onChange={(event) => usarPrimeiros(Number(event.target.value))} aria-label="Quantidade de itens" />
              </label>
              <strong>{escolhidos.length} un · {numero.format(qtd)} {unidadeOrigem}</strong>
            </div>
          </>
          : <>
            <label>
              Quantidade a usar ({unidadeOrigem})
              <input
                type="number"
                min="0"
                step="any"
                max={origem.quantidade}
                required
                value={quantidade}
                onChange={(event) => setQuantidade(event.target.value)}
                placeholder={`até ${numero.format(origem.quantidade)}`}
              />
            </label>
            <button type="button" className="text-button" onClick={() => setQuantidade(String(origem.quantidade))}>Usar todo o saldo</button>
            <div className="transfer-total"><span>Saldo disponível</span><strong>{numero.format(origem.quantidade)} {unidadeOrigem}</strong></div>
          </>}
      </section>

      <span className="transfer-arrow" aria-hidden="true">→</span>

      <section className="transfer-card">
        <div className="transfer-card-head"><h3>Destino</h3></div>
        {transformacao && <label>
          Produto resultante
          <SearchSelect<number | ''>
            required
            ariaLabel="Produto resultante"
            placeholder="Buscar produto"
            value={produtoDestinoId}
            onChange={(valor) => { setProdutoDestinoId(valor); setDestinoId('') }}
            options={opcoesDeProdutoResultante}
          />
        </label>}
        {transformacao
          ? <label>
            Lote de destino
            <SearchSelect<number | ''>
              required
              disabled={!produtoDestino}
              ariaLabel="Lote de destino"
              placeholder={produtoDestino ? 'Buscar lote' : 'Escolha o produto resultante'}
              value={destinoId}
              onChange={setDestinoId}
              options={[{ value: '', label: lotesDestino.length ? 'Selecione um lote existente' : 'Nenhum lote compatível' }, ...lotesDestino.map((lote) => ({
                value: lote.id,
                label: `#${lote.id} — ${caminhoLocalizacao(lote.localizacao_id, contexto.locaisPorId, lote.localizacao)} · ${numero.format(lote.quantidade)} ${unidadeDestino}`,
              }))]}
            />
          </label>
          : <label>
            Localização de destino
            <SearchSelect<number | ''>
              required
              ariaLabel="Localização de destino"
              placeholder="Buscar localização"
              value={localizacaoDestinoId}
              onChange={setLocalizacaoDestinoId}
              options={[{ value: '', label: 'Selecione' }, ...localizacoesDestino.map((local) => ({
                value: local.id,
                label: caminhoLocalizacao(local.id, contexto.locaisPorId, local.nome),
              }))]}
            />
            <small>Um novo lote será criado automaticamente, mantendo produto, validade e rastreabilidade da origem.</small>
          </label>}
        {transformacao && <label>
          Rendimento ({unidadeDestino || 'un. do produto'})
          <input type="number" min="0" step="any" required value={rendimento} onChange={(event) => setRendimento(event.target.value)} placeholder="Quantidade obtida" />
        </label>}
        <label>
          <RotuloDoCampo texto="Observação" opcional />
          <input value={observacao} onChange={(event) => setObservacao(event.target.value)} />
        </label>
        {transformacao && produtoDestino && !lotesDestino.length && <p className="helper">Cadastre antes um lote de {produtoDestino.nome} pelo botão “+ Novo lote”.</p>}
      </section>
    </div>

    <div className="transfer-summary">
      <div><span>Lote #{origem.id} depois da operação</span><strong>{resumoDaOrigem}</strong></div>
      <div><span>Destino recebe</span><strong>{destinoRecebe}</strong></div>
      <div><span>{transformacao ? 'Rendimento' : 'Destino'}</span><strong>{resumoFinal}</strong></div>
    </div>
  </form>
}
