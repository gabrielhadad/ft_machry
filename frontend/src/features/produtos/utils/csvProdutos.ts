import type { Conservacao, TipoProduto } from '../../../types'
import { lerCsv } from '../../../utils/csv'
import { normalizarChave } from '../../../utils/texto'
import { unidadesPermitidas } from '../unidades'

export const csvColunas = ['nome', 'tipo', 'unidade_medida', 'subdivisao', 'conservacao', 'validade_obrigatoria', 'validade_padrao_dias'] as const

export const csvModelo = [
  csvColunas.join(';'),
  'Farinha de trigo;INSUMO;kg;tipo 1;SECO;0;180',
  'Molho de tomate;INTERMEDIARIO;L;;RESFRIADO;1;5',
  'Lasanha;FINAL;un;;CONGELADO;1;30',
  '',
].join('\n')

const tiposCsv: Record<string, TipoProduto> = {
  INSUMO: 'INSUMO',
  INSUMOS: 'INSUMO',
  INTERMEDIARIO: 'INTERMEDIARIO',
  INTERMEDIARIOS: 'INTERMEDIARIO',
  FINAL: 'FINAL',
  'PRODUTO FINAL': 'FINAL',
  'PRODUTOS FINAIS': 'FINAL',
}
const conservacoesCsv: Record<string, Conservacao> = { SECO: 'SECO', RESFRIADO: 'RESFRIADO', CONGELADO: 'CONGELADO' }
const simCsv = new Set(['1', 'SIM', 'S', 'TRUE', 'X'])
const naoCsv = new Set(['', '0', 'NAO', 'N', 'FALSE'])

export type LinhaCsv = { linha: number; dados: Record<string, unknown>; erros: string[] }

export function converterProdutosCsv(texto: string): { linhas: LinhaCsv[]; erro?: string } {
  const [cabecalho, ...corpo] = lerCsv(texto)
  if (!cabecalho) return { linhas: [], erro: 'Arquivo vazio.' }
  const indices = cabecalho.map((coluna) => coluna.trim().toLowerCase())
  const faltando = ['nome', 'tipo', 'unidade_medida'].filter((coluna) => !indices.includes(coluna))
  if (faltando.length) return { linhas: [], erro: `Colunas obrigatórias ausentes: ${faltando.join(', ')}.` }
  const desconhecidas = indices.filter((coluna) => coluna && !(csvColunas as readonly string[]).includes(coluna))
  if (desconhecidas.length) return { linhas: [], erro: `Colunas desconhecidas: ${desconhecidas.join(', ')}.` }
  const linhas = corpo.map((valores, posicao) => ({ valores, linha: posicao + 2 }))
    .filter(({ valores }) => valores.some((valor) => valor.trim()))
    .map(({ valores, linha }) => {
      const valor = (coluna: string) => (valores[indices.indexOf(coluna)] ?? '').trim()
      const erros: string[] = []
      const nome = valor('nome')
      const unidade = valor('unidade_medida')
      const subdivisao = valor('subdivisao')
      if (!nome) erros.push('nome vazio')
      else if (nome.length > 150) erros.push('nome com mais de 150 caracteres')
      if (!unidade) erros.push('unidade vazia')
      else if (!unidadesPermitidas.has(unidade)) erros.push(`unidade inválida “${unidade}”`)
      if (subdivisao.length > 100) erros.push('subdivisão com mais de 100 caracteres')
      const tipo = tiposCsv[normalizarChave(valor('tipo'))]
      if (!tipo) erros.push(`tipo inválido “${valor('tipo')}”`)
      const conservacao = valor('conservacao') ? conservacoesCsv[normalizarChave(valor('conservacao'))] : 'SECO'
      if (!conservacao) erros.push(`conservação inválida “${valor('conservacao')}”`)
      const obrigatoria = normalizarChave(valor('validade_obrigatoria'))
      if (!simCsv.has(obrigatoria) && !naoCsv.has(obrigatoria)) erros.push(`validade obrigatória inválida “${valor('validade_obrigatoria')}”`)
      const dias = valor('validade_padrao_dias')
      if (dias && !/^\d+$/.test(dias)) erros.push(`validade padrão inválida “${dias}”`)
      const dados = {
        nome,
        tipo,
        unidade_medida: unidade,
        subdivisao: subdivisao || null,
        conservacao,
        validade_obrigatoria: simCsv.has(obrigatoria) ? 1 : 0,
        validade_padrao_dias: /^\d+$/.test(dias) ? Number(dias) : null,
      }
      return { linha, erros, dados }
    })
  if (!linhas.length) return { linhas, erro: 'Nenhum produto encontrado no arquivo.' }
  if (linhas.length > 500) return { linhas: [], erro: 'Limite de 500 produtos por importação.' }
  return { linhas }
}
