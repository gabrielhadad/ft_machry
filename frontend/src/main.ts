import './styles.css'
import type { AppState, FaseCatalogo, FichaComponente, FichaFase, FichaTecnica, ItemInventario, Produto, SolicitacaoProducao, View } from './types'

const state: AppState = { produtos: [], fichas: [], fases: [], inventario: [], solicitacoes: [], view: 'inicio', fichaEditando: null, produtoEditando: null }
const $ = (selector: string, root: ParentNode = document): any => root.querySelector(selector)
const $$ = (selector: string, root: ParentNode = document): any[] => [...root.querySelectorAll(selector)]
let toastTimer: ReturnType<typeof setTimeout> | undefined
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char])
const number = value => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 }).format(Number(value))

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response
  try {
    response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } })
  } catch {
    throw new Error('Não foi possível conectar à API.')
  }
  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) throw new Error(body?.erro || `Erro HTTP ${response.status}`)
  return body
}

function toast(message: string, error = false) {
  const element = $('#toast')
  element.textContent = message
  element.className = `toast show${error ? ' error' : ''}`
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { element.className = 'toast' }, 3600)
}

document.querySelector('#app').innerHTML = `
  <div class="layout">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">M</span><div><strong>Machry</strong><small>operação de cozinha</small></div></div>
      <p class="nav-caption">ÁREA DE TRABALHO</p>
      <nav>
        <button class="nav active" data-view="inicio"><span>⌂</span> Visão geral</button>
        <button class="nav" data-view="produtos"><span>◇</span> Produtos</button>
        <button class="nav" data-view="fichas"><span>≡</span> Fichas técnicas</button>
        <button class="nav" data-view="estoque"><span>▤</span> Estoque</button>
        <button class="nav" data-view="producao"><span>◷</span> Produção</button>
        <p class="nav-caption secondary-caption">GESTÃO</p>
        <button class="nav planned" disabled><span>☷</span> Pedidos <small>em breve</small></button>
        <button class="nav planned" disabled><span>◫</span> Compras <small>em breve</small></button>
        <button class="nav planned" disabled><span>◎</span> Financeiro <small>em breve</small></button>
        <button class="nav planned" disabled><span>⌁</span> Relatórios <small>em breve</small></button>
        <button class="nav planned" disabled><span>♙</span> Equipe <small>em breve</small></button>
        <a class="nav" href="/docs" target="_blank"><span>↗</span> Documentação</a>
      </nav>
      <div class="api-state"><i></i><div><strong>API Flask</strong><small id="apiState">conectando...</small></div></div>
    </aside>
    <main>
      <header><button class="menu" aria-label="Abrir menu">☰</button><div><small>RESTAURANTE MACHRY</small><strong id="pageName">Visão geral</strong></div><span class="environment">SQLite · Docker</span></header>
      <section id="content" class="content"></section>
    </main>
  </div>
  <dialog id="fichaDialog" class="dialog wide"></dialog>
  <dialog id="produtoDialog" class="dialog"></dialog>
  <div id="toast" class="toast" role="status"></div>
`

function metric(label: string, value: string | number, note: string) {
  return `<article class="metric"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`
}

function renderInicio() {
  const semFicha = state.produtos.filter(p => p.tipo !== 'INSUMO' && !state.fichas.some(f => f.produto_id === p.id)).length
  $('#content').innerHTML = `
    <div class="hero"><div><span class="eyebrow">OPERAÇÃO CENTRALIZADA</span><h1>A cozinha começa com<br><em>dados confiáveis.</em></h1><p>Produtos, receitas e rendimento em uma base pronta para acompanhar toda a produção.</p></div><button class="primary" data-action="nova-ficha">＋ Nova ficha técnica</button></div>
    <div class="metrics">
      ${metric('PRODUTOS ATIVOS', state.produtos.length, 'itens no catálogo')}
      ${metric('FICHAS TÉCNICAS', state.fichas.length, 'receitas padronizadas')}
      ${metric('SEM FICHA', semFicha, 'intermediários e finais')}
    </div>
    <section class="panel"><div class="panel-title"><div><span class="eyebrow">RECEITAS RECENTES</span><h2>Fichas em operação</h2></div><button class="secondary" data-view="fichas">Ver todas</button></div>${cardsFichas(state.fichas.slice(0, 3))}</section>
  `
}

function cardsFichas(fichas: FichaTecnica[]) {
  if (!fichas.length) return '<div class="empty">Nenhuma ficha técnica cadastrada.</div>'
  return `<div class="recipe-grid">${fichas.map(ficha => `
    <article class="recipe-card">
      <span class="type">${escapeHtml(state.produtos.find(p => p.id === ficha.produto_id)?.tipo || '')}</span>
      <h3>${escapeHtml(ficha.produto)}</h3>
      <p>Rende <b>${number(ficha.rendimento)} ${escapeHtml(ficha.unidade_rendimento)}</b></p>
      <div><span>${ficha.componentes.length} componentes</span><span>${ficha.fases.length} fases</span></div>
      <button class="text-button" data-edit-ficha="${ficha.id}">Ver e editar →</button>
    </article>`).join('')}</div>`
}

function renderProdutos() {
  $('#content').innerHTML = `
    <div class="page-heading"><div><span class="eyebrow">CATÁLOGO</span><h1>Produtos <em>& ingredientes</em></h1><p>Itens utilizados nas fichas e movimentações de estoque.</p></div><button class="primary" data-action="novo-produto">＋ Novo produto</button></div>
    <section class="panel"><div class="toolbar"><input id="productSearch" placeholder="Buscar produto..."><span>${state.produtos.length} ativos</span></div><div class="table-wrap"><table><thead><tr><th>Produto</th><th>Tipo</th><th>Unidade</th><th>Conservação</th><th></th></tr></thead><tbody>${state.produtos.map(p => `<tr><td><strong>${escapeHtml(p.nome)}</strong></td><td><span class="badge ${p.tipo.toLowerCase()}">${escapeHtml(p.tipo)}</span></td><td>${escapeHtml(p.unidade_medida)}</td><td>${escapeHtml(p.conservacao)}</td><td><button class="text-button" data-edit-produto="${p.id}">Editar</button></td></tr>`).join('')}</tbody></table></div></section>
  `
  $('#productSearch').addEventListener('input', event => {
    const query = event.target.value.trim().toLocaleLowerCase('pt-BR')
    $$('tbody tr').forEach(row => { row.hidden = !row.textContent.toLocaleLowerCase('pt-BR').includes(query) })
  })
}

function renderFichas() {
  $('#content').innerHTML = `
    <div class="page-heading"><div><span class="eyebrow">PADRONIZAÇÃO</span><h1>Fichas <em>técnicas</em></h1><p>Defina rendimento, componentes e sequência de produção.</p></div><button class="primary" data-action="nova-ficha">＋ Nova ficha técnica</button></div>
    <section class="panel">${cardsFichas(state.fichas)}</section>
  `
}

function renderEstoque() {
  const total = state.inventario.reduce((soma, item) => soma + Number(item.quantidade), 0)
  $('#content').innerHTML = `
    <div class="page-heading"><div><span class="eyebrow">RASTREABILIDADE</span><h1>Estoque <em>& lotes</em></h1><p>Saldo disponível por produto, lote e localização.</p></div></div>
    <div class="metrics">${metric('LOTES COM SALDO', state.inventario.length, 'disponíveis para uso')}${metric('SALDO SOMADO', number(total), 'em diferentes unidades')}${metric('PRODUTOS', new Set(state.inventario.map(item => item.produto_id)).size, 'com estoque disponível')}</div>
    <section class="panel"><div class="table-wrap"><table><thead><tr><th>Produto</th><th>Lote</th><th>Quantidade</th><th>Localização</th><th>Validade</th></tr></thead><tbody>${state.inventario.length ? state.inventario.map(item => `<tr><td><strong>${escapeHtml(item.produto)}</strong></td><td>#${item.lote_id}</td><td>${number(item.quantidade)} ${escapeHtml(item.unidade_medida)}</td><td>${escapeHtml(item.localizacao)}</td><td>${escapeHtml(item.data_validade || 'Sem validade')}</td></tr>`).join('') : '<tr><td colspan="5" class="empty">Nenhum lote possui saldo disponível.</td></tr>'}</tbody></table></div></section>`
}

function renderProducao() {
  $('#content').innerHTML = `
    <div class="page-heading"><div><span class="eyebrow">COZINHA</span><h1>Produção <em>em andamento</em></h1><p>Acompanhe as solicitações abertas a partir das fichas técnicas.</p></div></div>
    <div class="metrics">${metric('SOLICITAÇÕES', state.solicitacoes.length, 'registros de produção')}${metric('EM PRODUÇÃO', state.solicitacoes.filter(item => item.status === 'EM_PRODUCAO').length, 'em execução agora')}${metric('CONCLUÍDAS', state.solicitacoes.filter(item => item.status === 'CONCLUIDA').length, 'produção finalizada')}</div>
    <section class="panel"><div class="table-wrap"><table><thead><tr><th>Solicitação</th><th>Ficha</th><th>Status</th><th>Criada em</th></tr></thead><tbody>${state.solicitacoes.length ? state.solicitacoes.map(item => `<tr><td><strong>#${item.id}</strong></td><td>#${item.ficha_tecnica_id}</td><td><span class="badge intermediario">${escapeHtml(item.status)}</span></td><td>${escapeHtml(item.criado_em)}</td></tr>`).join('') : '<tr><td colspan="4" class="empty">Nenhuma solicitação de produção cadastrada.</td></tr>'}</tbody></table></div></section>`
}

function navigate(view: View) {
  state.view = view
  $$('.nav[data-view]').forEach(item => item.classList.toggle('active', item.dataset.view === view))
  $('#pageName').textContent = ({ inicio: 'Visão geral', produtos: 'Produtos', fichas: 'Fichas técnicas', estoque: 'Estoque', producao: 'Produção' })[view]
  ;({ inicio: renderInicio, produtos: renderProdutos, fichas: renderFichas, estoque: renderEstoque, producao: renderProducao })[view]()
  $('.sidebar').classList.remove('open')
}

function produtoOptions(selected?: number, filter: (produto: Produto) => boolean = () => true) {
  return state.produtos.filter(filter).map(p => `<option value="${p.id}" ${p.id === Number(selected) ? 'selected' : ''}>${escapeHtml(p.nome)} · ${escapeHtml(p.unidade_medida)}</option>`).join('')
}

function phaseRow(data: Partial<FichaFase> = {}) {
  return `<div class="form-row phase-row"><label>Ordem<input class="phase-order" type="number" min="1" required value="${data.ordem ?? ''}"></label><label>Fase<select class="phase-id" required><option value="">Selecione</option>${state.fases.map(f => `<option value="${f.id}" ${f.id === data.fase_id ? 'selected' : ''}>${escapeHtml(f.nome)}</option>`).join('')}</select></label><label>Tempo (min)<input class="phase-time" type="number" min="1" required value="${data.tempo_previsto_min ?? ''}"></label><button type="button" class="remove-row" title="Remover">×</button></div>`
}

function componentRow(data: Partial<FichaComponente> = {}) {
  return `<div class="form-row component-row"><label>Componente<select class="component-id" required><option value="">Selecione</option>${produtoOptions(data.produto_id)}</select></label><label>Quantidade<input class="component-quantity" type="number" min="0.001" step="0.001" required value="${data.quantidade ?? ''}"></label><label>Fase<select class="component-phase"><option value="">Sem fase</option></select></label><button type="button" class="remove-row" title="Remover">×</button></div>`
}

function syncComponentPhases(root, values = new Map()) {
  const ordens = $$('.phase-order', root).map(input => input.value).filter(Boolean)
  $$('.component-phase', root).forEach((select, index) => {
    const current = values.has(index) ? String(values.get(index) ?? '') : select.value
    select.innerHTML = '<option value="">Sem fase</option>' + ordens.map(ordem => `<option value="${ordem}">${ordem}</option>`).join('')
    select.value = current
  })
}

function openFicha(ficha: FichaTecnica | null = null) {
  state.fichaEditando = ficha?.id ?? null
  const dialog = $('#fichaDialog')
  dialog.innerHTML = `<form id="fichaForm"><div class="dialog-head"><div><span class="eyebrow">FICHA TÉCNICA</span><h2>${ficha ? 'Editar receita' : 'Nova receita'}</h2></div><button type="button" class="icon-button" data-close>×</button></div><div class="dialog-body"><div class="form-grid"><label>Produto resultante<select name="produto_id" required><option value="">Selecione</option>${produtoOptions(ficha?.produto_id, p => p.tipo !== 'INSUMO')}</select></label><label>Rendimento<input name="rendimento" type="number" min="0.001" step="0.001" required value="${ficha?.rendimento ?? ''}"></label></div><label>Observação<textarea name="observacao" rows="2" placeholder="Instruções gerais ou observações">${escapeHtml(ficha?.observacao || '')}</textarea></label><div class="subsection"><div><h3>Fases de produção</h3><button type="button" class="text-button" id="addPhase">＋ Adicionar fase</button></div><div id="phaseRows">${(ficha?.fases || [{}]).map(phaseRow).join('')}</div></div><div class="subsection"><div><h3>Componentes</h3><button type="button" class="text-button" id="addComponent">＋ Adicionar componente</button></div><div id="componentRows">${(ficha?.componentes || [{}]).map(componentRow).join('')}</div></div><p id="fichaError" class="form-error" hidden></p></div><div class="dialog-actions">${ficha ? '<button type="button" class="danger-link" id="deleteFicha">Excluir ficha</button>' : '<span></span>'}<button type="button" class="secondary" data-close>Cancelar</button><button type="submit" class="primary">Salvar ficha</button></div></form>`
  const phaseValues = new Map((ficha?.componentes || []).map((item, index) => [index, item.fase_ordem]))
  syncComponentPhases(dialog, phaseValues)
  dialog.showModal()
  $$('[data-close]', dialog).forEach(button => button.onclick = () => dialog.close())
  $('#addPhase', dialog).onclick = () => { $('#phaseRows', dialog).insertAdjacentHTML('beforeend', phaseRow()); syncComponentPhases(dialog) }
  $('#addComponent', dialog).onclick = () => { $('#componentRows', dialog).insertAdjacentHTML('beforeend', componentRow()); syncComponentPhases(dialog) }
  dialog.oninput = event => { if ((event.target as Element).classList.contains('phase-order')) syncComponentPhases(dialog) }
  dialog.onclick = event => { const button = (event.target as Element).closest('.remove-row'); if (button) { button.parentElement?.remove(); syncComponentPhases(dialog) } }
  $('#fichaForm', dialog).onsubmit = saveFicha
  if (ficha) $('#deleteFicha', dialog).onclick = () => deleteFicha(ficha)
}

async function saveFicha(event) {
  event.preventDefault()
  const dialog = $('#fichaDialog')
  const form = event.currentTarget
  const payload = {
    produto_id: Number(form.elements.produto_id.value),
    rendimento: Number(form.elements.rendimento.value),
    observacao: form.elements.observacao.value.trim() || null,
    fases: $$('.phase-row', dialog).map(row => ({ fase_id: Number($('.phase-id', row).value), ordem: Number($('.phase-order', row).value), tempo_previsto_min: Number($('.phase-time', row).value) })),
    componentes: $$('.component-row', dialog).map(row => ({ produto_id: Number($('.component-id', row).value), quantidade: Number($('.component-quantity', row).value), fase_ordem: $('.component-phase', row).value ? Number($('.component-phase', row).value) : null })),
  }
  const error = $('#fichaError', dialog)
  try {
    await api(`/api/fichas-tecnicas${state.fichaEditando ? `/${state.fichaEditando}` : ''}`, { method: state.fichaEditando ? 'PUT' : 'POST', body: JSON.stringify(payload) })
    dialog.close(); await reload(); navigate('fichas'); toast('Ficha técnica salva com sucesso.')
  } catch (exception) { error.textContent = exception.message; error.hidden = false }
}

async function deleteFicha(ficha) {
  if (!confirm(`Excluir a ficha de “${ficha.produto}”?`)) return
  try { await api(`/api/fichas-tecnicas/${ficha.id}`, { method: 'DELETE' }); $('#fichaDialog').close(); await reload(); navigate('fichas'); toast('Ficha excluída.') } catch (error) { toast(error.message, true) }
}

function openProduto(produto: Produto | null = null) {
  state.produtoEditando = produto?.id ?? null
  const dialog = $('#produtoDialog')
  dialog.innerHTML = `<form id="produtoForm"><div class="dialog-head"><div><span class="eyebrow">CATÁLOGO</span><h2>${produto ? 'Editar produto' : 'Novo produto'}</h2></div><button type="button" class="icon-button" data-close>×</button></div><div class="dialog-body"><label>Nome<input name="nome" required value="${escapeHtml(produto?.nome || '')}"></label><div class="form-grid"><label>Tipo<select name="tipo"><option value="INSUMO">Insumo</option><option value="INTERMEDIARIO">Intermediário</option><option value="FINAL">Final</option></select></label><label>Unidade<input name="unidade_medida" required value="${escapeHtml(produto?.unidade_medida || '')}" placeholder="g, kg, ml, un"></label></div><div class="form-grid"><label>Conservação<select name="conservacao"><option value="SECO">Seco</option><option value="RESFRIADO">Resfriado</option><option value="CONGELADO">Congelado</option></select></label><label>Validade padrão (dias)<input name="validade_padrao_dias" type="number" min="0" value="${produto?.validade_padrao_dias ?? ''}"></label></div><label class="checkbox"><input name="validade_obrigatoria" type="checkbox"> Validade obrigatória nos lotes</label><p id="produtoError" class="form-error" hidden></p></div><div class="dialog-actions"><span></span><button type="button" class="secondary" data-close>Cancelar</button><button type="submit" class="primary">Salvar produto</button></div></form>`
  const form = $('#produtoForm', dialog)
  form.elements.tipo.value = produto?.tipo || 'INSUMO'; form.elements.conservacao.value = produto?.conservacao || 'SECO'; form.elements.validade_obrigatoria.checked = Boolean(produto?.validade_obrigatoria)
  $$('[data-close]', dialog).forEach(button => button.onclick = () => dialog.close())
  form.onsubmit = saveProduto
  dialog.showModal()
}

async function saveProduto(event) {
  event.preventDefault()
  const form = event.currentTarget
  const payload = { nome: form.elements.nome.value.trim(), tipo: form.elements.tipo.value, unidade_medida: form.elements.unidade_medida.value.trim(), conservacao: form.elements.conservacao.value, validade_obrigatoria: form.elements.validade_obrigatoria.checked ? 1 : 0, validade_padrao_dias: form.elements.validade_padrao_dias.value ? Number(form.elements.validade_padrao_dias.value) : null }
  try { await api(`/api/produtos${state.produtoEditando ? `/${state.produtoEditando}` : ''}`, { method: state.produtoEditando ? 'PUT' : 'POST', body: JSON.stringify(payload) }); $('#produtoDialog').close(); await reload(); navigate('produtos'); toast('Produto salvo com sucesso.') } catch (error) { const target = $('#produtoError'); target.textContent = error.message; target.hidden = false }
}

document.addEventListener('click', event => {
  const target = event.target as Element
  const view = target.closest<HTMLElement>('[data-view]')?.dataset.view as View | undefined
  if (view) navigate(view)
  if (target.closest('[data-action="nova-ficha"]')) openFicha()
  if (target.closest('[data-action="novo-produto"]')) openProduto()
  const fichaId = target.closest<HTMLElement>('[data-edit-ficha]')?.dataset.editFicha
  if (fichaId) openFicha(state.fichas.find(ficha => ficha.id === Number(fichaId)))
  const produtoId = target.closest<HTMLElement>('[data-edit-produto]')?.dataset.editProduto
  if (produtoId) openProduto(state.produtos.find(produto => produto.id === Number(produtoId)))
})
$('.menu').onclick = () => $('.sidebar').classList.toggle('open')

async function reload() {
  const [produtos, fichas, fases, inventario, solicitacoes] = await Promise.all([api<Produto[]>('/api/produtos'), api<FichaTecnica[]>('/api/fichas-tecnicas'), api<FaseCatalogo[]>('/api/fichas-tecnicas/fases'), api<ItemInventario[]>('/api/estoque/inventario'), api<SolicitacaoProducao[]>('/api/producao/solicitacoes')])
  Object.assign(state, { produtos, fichas, fases, inventario, solicitacoes })
}

try { await reload(); $('#apiState').textContent = 'conectada'; navigate('inicio') } catch (error) { $('#apiState').textContent = 'indisponível'; $('#content').innerHTML = `<div class="load-error"><h1>Não foi possível abrir o painel</h1><p>${escapeHtml(error.message)}</p><p>Inicialize o banco e confirme se o container da API está ativo.</p></div>` }
