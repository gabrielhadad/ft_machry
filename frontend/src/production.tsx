import { useState, type FormEvent } from 'react'
import { api } from './api'
import { EmptyState, Metric, Modal, PageHeading } from './components'
import type {
  FichaTecnica,
  FaseSolicitacao,
  Localizacao,
  PlanejamentoProducaoInput,
  SolicitacaoDetalhe,
  SolicitacaoProducao,
  Usuario,
} from './types'

const number = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 })
const dateTime = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
const priorityLabel: Record<SolicitacaoProducao['prioridade'], string> = {
  BAIXA: 'Baixa', NORMAL: 'Normal', ALTA: 'Alta', URGENTE: 'Urgente',
}

function formatDate(value: string | null) {
  if (!value) return '—'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : dateTime.format(parsed)
}

function localDateTime(value: string | null) {
  if (!value) return ''
  return value.slice(0, 16)
}

type PhaseDraft = {
  tempo: string
  observacao: string
  inicio: string
  fim: string
}

type LossDraft = { quantidade: string; motivo: string }

export function ProductionPage({
  solicitacoes,
  fichas,
  localizacoes,
  responsaveis,
  canPlan,
  onChanged,
}: {
  solicitacoes: SolicitacaoProducao[]
  fichas: FichaTecnica[]
  localizacoes: Localizacao[]
  responsaveis: Usuario[]
  canPlan: boolean
  onChanged: () => Promise<void>
}) {
  const productBySheet = new Map(fichas.map((ficha) => [ficha.id, ficha.produto]))
  const [selectedSheet, setSelectedSheet] = useState(fichas[0]?.id ?? 0)
  const selectedFicha = fichas.find((item) => item.id === selectedSheet)
  const [quantity, setQuantity] = useState(selectedFicha?.rendimento ?? 1)
  const [priority, setPriority] = useState<SolicitacaoProducao['prioridade']>('NORMAL')
  const [scheduledFor, setScheduledFor] = useState('')
  const [responsible, setResponsible] = useState('')
  const [planningNote, setPlanningNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null)
  const [detail, setDetail] = useState<SolicitacaoDetalhe | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [produced, setProduced] = useState('')
  const [executionNote, setExecutionNote] = useState('')
  const [phaseDrafts, setPhaseDrafts] = useState<Record<number, PhaseDraft>>({})
  const [lossDrafts, setLossDrafts] = useState<Record<number, LossDraft>>({})
  const [destination, setDestination] = useState('')

  const changeSheet = (id: number) => {
    setSelectedSheet(id)
    const ficha = fichas.find((item) => item.id === id)
    if (ficha) setQuantity(ficha.rendimento)
  }

  const create = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedSheet) return
    setSubmitting(true); setMessage(null)
    try {
      const payload: PlanejamentoProducaoInput = {
        ficha_tecnica_id: selectedSheet,
        quantidade_planejada: quantity,
        prioridade: priority,
        previsto_para: scheduledFor || null,
        responsavel_id: responsible ? Number(responsible) : null,
        observacao: planningNote.trim() || null,
      }
      await api('/api/producao/solicitacoes', { method: 'POST', body: JSON.stringify(payload) })
      await onChanged()
      setPlanningNote(''); setScheduledFor(''); setResponsible(''); setPriority('NORMAL')
      setMessage({ text: 'Produção planejada e adicionada à fila.' })
    } catch (reason) {
      setMessage({ text: reason instanceof Error ? reason.message : 'Não foi possível planejar a produção.', error: true })
    } finally { setSubmitting(false) }
  }

  const updateStatus = async (id: number, status: string, localizacaoDestino?: number) => {
    setSubmitting(true); setMessage(null)
    try {
      await api(`/api/producao/solicitacoes/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status, localizacao_destino_id: localizacaoDestino ?? null }),
      })
      await onChanged()
      setMessage({ text: status === 'CONCLUIDA' ? 'Produção concluída e estoque atualizado.' : 'Produção iniciada.' })
      if (detail?.solicitacao.id === id) await openDetail(id)
    } catch (reason) {
      setMessage({ text: reason instanceof Error ? reason.message : 'Não foi possível atualizar a produção.', error: true })
    } finally { setSubmitting(false) }
  }

  const loadDrafts = (data: SolicitacaoDetalhe) => {
    setProduced(data.solicitacao.quantidade_produzida?.toString() ?? '')
    setExecutionNote(data.solicitacao.observacao_execucao ?? '')
    setPhaseDrafts(Object.fromEntries(data.fases.map((fase) => [fase.sp_fase_id, {
      tempo: fase.tempo_realizado_min?.toString() ?? '',
      observacao: fase.observacao ?? '',
      inicio: localDateTime(fase.iniciado_em),
      fim: localDateTime(fase.finalizado_em),
    }])))
    setLossDrafts({})
  }

  const openDetail = async (id: number) => {
    setDetailLoading(true); setMessage(null)
    try {
      const data = await api<SolicitacaoDetalhe>(`/api/producao/solicitacoes/${id}`)
      setDetail(data); loadDrafts(data)
    } catch (reason) {
      setMessage({ text: reason instanceof Error ? reason.message : 'Não foi possível abrir a produção.', error: true })
    } finally { setDetailLoading(false) }
  }

  const updatePhaseDraft = (fase: FaseSolicitacao, change: Partial<PhaseDraft>) => {
    setPhaseDrafts((current) => ({ ...current, [fase.sp_fase_id]: { ...current[fase.sp_fase_id], ...change } }))
  }

  const saveExecution = async () => {
    if (!detail) return
    setSubmitting(true); setMessage(null)
    try {
      const phases = detail.fases.flatMap((fase) => {
        const row = phaseDrafts[fase.sp_fase_id]
        if (!row || (!row.tempo && !row.observacao.trim() && !row.inicio && !row.fim)) return []
        return [{
          sp_fase_id: fase.sp_fase_id,
          tempo_realizado_min: row.tempo === '' ? null : Number(row.tempo),
          observacao: row.observacao.trim() || null,
          iniciado_em: row.inicio || null,
          finalizado_em: row.fim || null,
        }]
      })
      const perdas = detail.componentes.flatMap((component) => {
        const row = lossDrafts[component.sp_componente_id]
        if (!row?.quantidade) return []
        return [{ sp_componente_id: component.sp_componente_id, quantidade: Number(row.quantidade), motivo: row.motivo.trim() }]
      })
      const payload = {
        quantidade_produzida: produced === '' ? null : Number(produced),
        observacao_execucao: executionNote.trim() || null,
        fases: phases,
        perdas,
      }
      const updated = await api<SolicitacaoDetalhe>(`/api/producao/solicitacoes/${detail.solicitacao.id}/execucao`, {
        method: 'PUT', body: JSON.stringify(payload),
      })
      setDetail(updated); loadDrafts(updated); await onChanged()
      setMessage({ text: 'Execução registrada. Planejado e realizado foram preservados.' })
    } catch (reason) {
      setMessage({ text: reason instanceof Error ? reason.message : 'Não foi possível registrar a execução.', error: true })
    } finally { setSubmitting(false) }
  }

  const complete = async () => {
    if (!detail) return
    await updateStatus(detail.solicitacao.id, 'CONCLUIDA', destination ? Number(destination) : undefined)
  }

  const activeCount = solicitacoes.filter((item) => !['CONCLUIDA', 'CANCELADA'].includes(item.status)).length
  const urgentCount = solicitacoes.filter((item) => item.prioridade === 'URGENTE' && !['CONCLUIDA', 'CANCELADA'].includes(item.status)).length

  return <>
    <PageHeading eyebrow="COZINHA" title="Produção" description="Planeje, execute e compare o previsto com o realizado sem perder o histórico." action={<button className="secondary no-print" onClick={() => window.print()}>Imprimir fila</button>} />
    <section className="metrics"><Metric label="SOLICITAÇÕES" value={solicitacoes.length} detail="total registrado" /><Metric label="EM ANDAMENTO" value={activeCount} detail="aguardando conclusão" /><Metric label="URGENTES" value={urgentCount} detail="prioridade máxima" /></section>
    {message && <p className={message.error ? 'production-message error' : 'production-message'}>{message.text}</p>}

    {canPlan && <section className="panel production-planner-v2"><div className="planner-heading"><span className="eyebrow">PLANEJAMENTO</span><h2>Nova produção</h2><p>Defina quantidade, prioridade, horário e responsável antes de enviar para a cozinha.</p></div><form className="planning-form" onSubmit={create}>
      <label>Ficha técnica<select value={selectedSheet} onChange={(event) => changeSheet(Number(event.target.value))}>{fichas.map((ficha) => <option key={ficha.id} value={ficha.id}>{ficha.produto} · rende {number.format(ficha.rendimento)} {ficha.unidade_rendimento}</option>)}</select></label>
      <label>Quantidade planejada<input required min="0.001" step="any" type="number" value={quantity} onChange={(event) => setQuantity(Number(event.target.value))} /></label>
      <label>Prioridade<select value={priority} onChange={(event) => setPriority(event.target.value as SolicitacaoProducao['prioridade'])}><option value="BAIXA">Baixa</option><option value="NORMAL">Normal</option><option value="ALTA">Alta</option><option value="URGENTE">Urgente</option></select></label>
      <label>Previsto para<input type="datetime-local" value={scheduledFor} onChange={(event) => setScheduledFor(event.target.value)} /></label>
      <label>Responsável<select value={responsible} onChange={(event) => setResponsible(event.target.value)}><option value="">Definir depois</option>{responsaveis.map((user) => <option key={user.id} value={user.id}>{user.nome} · {user.papel}</option>)}</select></label>
      <label className="planning-note">Observação<textarea rows={2} value={planningNote} maxLength={2000} onChange={(event) => setPlanningNote(event.target.value)} placeholder="Orientações para a cozinha" /></label>
      <button className="primary" disabled={!selectedSheet || submitting}>Adicionar à fila</button>
    </form></section>}

    <section className="panel"><div className="table-wrap"><table><thead><tr><th>#</th><th>Produto</th><th>Planejado</th><th>Prioridade</th><th>Responsável</th><th>Previsto</th><th>Status</th><th>Ações</th></tr></thead><tbody>{solicitacoes.map((item) => <tr key={item.id}><td>#{item.id}</td><td><strong>{productBySheet.get(item.ficha_tecnica_id) || `Ficha #${item.ficha_tecnica_id}`}</strong></td><td>{number.format(item.quantidade_planejada)}</td><td><span className={`priority priority-${item.prioridade.toLowerCase()}`}>{priorityLabel[item.prioridade]}</span></td><td>{responsaveis.find((user) => user.id === item.responsavel_id)?.nome || (item.responsavel_id ? `Usuário #${item.responsavel_id}` : '—')}</td><td>{formatDate(item.previsto_para)}</td><td><span className={`badge status-${item.status.toLowerCase()}`}>{item.status.replaceAll('_', ' ')}</span></td><td className="production-actions">{['ABERTA', 'EM_SEPARACAO'].includes(item.status) && <button className="text-button" disabled={submitting} onClick={() => void updateStatus(item.id, 'EM_PRODUCAO')}>Iniciar</button>}<button className="text-button" disabled={detailLoading} onClick={() => void openDetail(item.id)}>Detalhes</button></td></tr>)}</tbody></table></div>{!solicitacoes.length && <EmptyState title="Nenhum preparo na fila" text="O gestor ainda não definiu a produção." />}</section>

    {detail && <Modal eyebrow="EXECUÇÃO" title={`${productBySheet.get(detail.solicitacao.ficha_tecnica_id) || 'Produção'} · #${detail.solicitacao.id}`} wide onClose={() => setDetail(null)} footer={<><button className="secondary" type="button" onClick={() => setDetail(null)}>Fechar</button>{detail.solicitacao.status === 'EM_PRODUCAO' && <button className="secondary" disabled={submitting} type="button" onClick={() => void saveExecution()}>Salvar execução</button>}{detail.solicitacao.status === 'EM_PRODUCAO' && <button className="primary" disabled={submitting} type="button" onClick={() => void complete()}>Concluir produção</button>}</>}>
      <div className="dialog-body production-detail">
        <section className="production-summary-grid"><div><span>PLANEJADO</span><strong>{number.format(detail.solicitacao.quantidade_planejada)}</strong></div><div><span>PRODUZIDO</span><strong>{detail.solicitacao.quantidade_produzida === null ? '—' : number.format(detail.solicitacao.quantidade_produzida)}</strong></div><div><span>PERDA DE RENDIMENTO</span><strong>{detail.solicitacao.perda_rendimento === null ? '—' : number.format(detail.solicitacao.perda_rendimento)}</strong></div><div><span>STATUS</span><strong>{detail.solicitacao.status.replaceAll('_', ' ')}</strong></div></section>
        {detail.solicitacao.observacao && <p className="production-note"><strong>Planejamento:</strong> {detail.solicitacao.observacao}</p>}

        {detail.solicitacao.status === 'EM_PRODUCAO' && <section className="execution-fields"><h3>Resultado da produção</h3><div className="form-grid"><label>Quantidade produzida<input type="number" min="0" step="any" value={produced} onChange={(event) => setProduced(event.target.value)} placeholder={detail.solicitacao.quantidade_planejada.toString()} /></label><label>Local de destino<select value={destination} onChange={(event) => setDestination(event.target.value)}><option value="">Automático (primeiro compatível)</option>{localizacoes.map((location) => <option key={location.id} value={location.id}>{location.nome} · {location.tipo}</option>)}</select></label></div><label>Observação da execução<textarea rows={2} maxLength={2000} value={executionNote} onChange={(event) => setExecutionNote(event.target.value)} /></label></section>}

        <section><h3>Etapas — planejado × realizado</h3><div className="production-phase-list">{detail.fases.map((fase) => { const row = phaseDrafts[fase.sp_fase_id] || { tempo: '', observacao: '', inicio: '', fim: '' }; return <article key={fase.sp_fase_id}><div className="phase-heading"><span>{fase.ordem}</span><strong>{fase.fase}</strong><small>Previsto: {fase.tempo_previsto_min} min</small></div>{detail.solicitacao.status === 'EM_PRODUCAO' ? <div className="phase-execution-grid"><label>Realizado (min)<input type="number" min="0" value={row.tempo} onChange={(event) => updatePhaseDraft(fase, { tempo: event.target.value })} /></label><label>Início<input type="datetime-local" value={row.inicio} onChange={(event) => updatePhaseDraft(fase, { inicio: event.target.value })} /></label><label>Fim<input type="datetime-local" value={row.fim} onChange={(event) => updatePhaseDraft(fase, { fim: event.target.value })} /></label><label className="phase-note">Observação<input value={row.observacao} onChange={(event) => updatePhaseDraft(fase, { observacao: event.target.value })} /></label></div> : <p>Realizado: <strong>{fase.tempo_realizado_min ?? '—'} min</strong>{fase.observacao ? ` · ${fase.observacao}` : ''}</p>}</article>})}</div></section>

        <section><h3>Componentes — planejado × realizado</h3><div className="table-wrap"><table><thead><tr><th>Componente</th><th>Planejado</th><th>Realizado</th><th>Variação</th></tr></thead><tbody>{detail.componentes.map((component) => <tr key={component.sp_componente_id}><td><strong>{component.componente}</strong></td><td>{number.format(component.quantidade_prevista)} {component.unidade_medida}</td><td>{number.format(component.quantidade_realizada)} {component.unidade_medida}</td><td>{number.format(component.quantidade_realizada - component.quantidade_prevista)} {component.unidade_medida}</td></tr>)}</tbody></table></div></section>

        {detail.solicitacao.status === 'EM_PRODUCAO' && <section><h3>Registrar novas perdas</h3><p className="helper">Perdas são baixadas imediatamente do estoque e ficam vinculadas a esta produção. Após salvar, os campos são limpos para evitar reenvio acidental.</p><div className="loss-grid">{detail.componentes.map((component) => { const row = lossDrafts[component.sp_componente_id] || { quantidade: '', motivo: '' }; return <div className="loss-row" key={component.sp_componente_id}><strong>{component.componente}</strong><label>Quantidade<input type="number" min="0" step="any" value={row.quantidade} onChange={(event) => setLossDrafts((current) => ({ ...current, [component.sp_componente_id]: { ...row, quantidade: event.target.value } }))} /></label><label>Motivo<input value={row.motivo} maxLength={500} onChange={(event) => setLossDrafts((current) => ({ ...current, [component.sp_componente_id]: { ...row, motivo: event.target.value } }))} placeholder="Ex.: derramamento" /></label></div>})}</div></section>}

        {!!detail.lotes_produzidos.length && <section><h3>Produto acabado</h3>{detail.lotes_produzidos.map((lot) => <p className="produced-lot" key={lot.lote_id}><strong>Lote #{lot.lote_id}</strong><span>{number.format(lot.quantidade)} produzidos</span><small>{formatDate(lot.criado_em)}</small></p>)}</section>}
      </div>
    </Modal>}
  </>
}
