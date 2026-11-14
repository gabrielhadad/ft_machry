import { lerCsv } from '../../../utils/csv'
import { normalizarChave } from '../../../utils/texto'

export const fichaColunas = ['ficha', 'rendimento', 'observacao', 'fase_ordem', 'fase', 'tempo_min', 'componente', 'quantidade', 'unidade'] as const

export const fichaModelo = [
  'ficha;rendimento;observacao;fase_ordem;fase;tempo_min;componente;quantidade;unidade',
  'Purê de batata;0,35;Cozinhe as batatas inteiras com sal.;1;Cozir;25;Batata asterix;300;g',
  'Purê de batata;;Aqueça a manteiga, a nata e o leite e junte as batatas.;2;Bater/Misturar;15;Nata;60;ml',
  'Purê de batata;;;2;;;Manteiga sem sal;15;g',
  'Purê de batata;;;;;;Sal fino;q.b.;',
  '',
].join('\n')

const aGosto = new Set(['', 'QB', 'Q.B', 'Q.B.', 'A GOSTO'])

export const numeroCsv = (valor: string) => /^\d+([.,]\d+)?$/.test(valor) ? Number(valor.replace(',', '.')) : NaN

export type FaseCsv = { fase: string; ordem: number; tempo_previsto_min: number }
export type ComponenteCsv = { produto: string; quantidade: string | null; unidade: string | null; fase_ordem: number | null }
export type FichaCsv = { nome: string; linhas: number[]; rendimento: string; observacoes: string[]; fases: Map<number, FaseCsv>; componentes: ComponenteCsv[]; erros: string[] }

export const fasesEmOrdem = (ficha: FichaCsv) => [...ficha.fases.values()].sort((a, b) => a.ordem - b.ordem)

export function converterFichasCsv(texto: string): { fichas: FichaCsv[]; erro?: string } {
  const [cabecalho, ...corpo] = lerCsv(texto)
  if (!cabecalho) return { fichas: [], erro: 'Arquivo vazio.' }
  const indices = cabecalho.map((coluna) => coluna.trim().toLowerCase())
  const faltando = ['ficha', 'rendimento', 'fase_ordem', 'fase', 'tempo_min', 'componente', 'quantidade'].filter((coluna) => !indices.includes(coluna))
  if (faltando.length) return { fichas: [], erro: `Colunas obrigatórias ausentes: ${faltando.join(', ')}.` }
  const desconhecidas = indices.filter((coluna) => coluna && !(fichaColunas as readonly string[]).includes(coluna))
  if (desconhecidas.length) return { fichas: [], erro: `Colunas desconhecidas: ${desconhecidas.join(', ')}.` }

  const porNome = new Map<string, FichaCsv>()
  corpo.forEach((valores, posicao) => {
    if (!valores.some((valor) => valor.trim())) return
    const linha = posicao + 2
    const valor = (coluna: string) => (valores[indices.indexOf(coluna)] ?? '').trim()
    const nome = valor('ficha')
    if (!nome) {
      porNome.set(`#${linha}`, { nome: `(linha ${linha})`, linhas: [linha], rendimento: '', observacoes: [], fases: new Map(), componentes: [], erros: ['nome da ficha vazio'] })
      return
    }
    const chave = normalizarChave(nome)
    const ficha: FichaCsv = porNome.get(chave) ?? { nome, linhas: [], rendimento: '', observacoes: [], fases: new Map(), componentes: [], erros: [] }
    porNome.set(chave, ficha)
    ficha.linhas.push(linha)
    const erro = (texto: string) => ficha.erros.push(`linha ${linha}: ${texto}`)

    const rendimento = valor('rendimento')
    if (rendimento) {
      if (!(numeroCsv(rendimento) > 0)) erro(`rendimento inválido “${rendimento}”`)
      else if (ficha.rendimento && ficha.rendimento !== rendimento) erro(`rendimento diferente do informado antes (${ficha.rendimento})`)
      else ficha.rendimento = rendimento
    }
    if (valor('observacao')) ficha.observacoes.push(valor('observacao'))

    const ordemTexto = valor('fase_ordem')
    const ordem = ordemTexto ? Number(ordemTexto) : null
    if (ordemTexto && !(Number.isInteger(ordem) && ordem! > 0)) erro(`ordem da fase inválida “${ordemTexto}”`)
    else if (ordem) {
      const existente = ficha.fases.get(ordem)
      const fase = valor('fase')
      const tempoTexto = valor('tempo_min')
      const tempo = Number(tempoTexto)
      if (tempoTexto && !(Number.isInteger(tempo) && tempo > 0)) erro(`tempo inválido “${tempoTexto}”`)
      if (existente) {
        if (fase && normalizarChave(fase) !== normalizarChave(existente.fase)) erro(`fase ${ordem} já definida como “${existente.fase}”`)
        if (tempoTexto && tempo !== existente.tempo_previsto_min) erro(`tempo da fase ${ordem} diferente do informado antes`)
      } else if (!fase || !tempoTexto) erro(`fase ${ordem} precisa de nome e tempo na primeira linha em que aparece`)
      else ficha.fases.set(ordem, { fase, ordem, tempo_previsto_min: tempo })
    } else if (valor('fase') || valor('tempo_min')) erro('fase sem fase_ordem')

    const componente = valor('componente')
    const quantidade = valor('quantidade')
    if (componente) {
      const qb = aGosto.has(normalizarChave(quantidade))
      if (!qb && !(numeroCsv(quantidade) > 0)) erro(`quantidade inválida “${quantidade}” para ${componente}`)
      else ficha.componentes.push({ produto: componente, quantidade: qb ? null : String(numeroCsv(quantidade)), unidade: valor('unidade') || null, fase_ordem: ordem })
    } else if (quantidade) erro('quantidade sem componente')
  })

  const fichas = [...porNome.values()]
  for (const ficha of fichas) {
    if (!ficha.rendimento) ficha.erros.push('rendimento não informado')
    if (!ficha.fases.size) ficha.erros.push('nenhuma fase informada')
    if (!ficha.componentes.some((item) => item.quantidade)) ficha.erros.push('nenhum componente com quantidade')
  }
  if (!fichas.length) return { fichas, erro: 'Nenhuma ficha encontrada no arquivo.' }
  if (fichas.length > 200) return { fichas: [], erro: 'Limite de 200 fichas por importação.' }
  return { fichas }
}
