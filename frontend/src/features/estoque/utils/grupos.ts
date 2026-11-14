import type { Grupo, NovoItem } from '../types'

let proximaChave = 1

export const grupoVazio = (): Grupo => ({
  chave: proximaChave++,
  unidades: '1',
  conteudo: '',
  fabricante: '',
  fabricacao: '',
  validade: '',
  validadeManual: false,
})

export const numeroDe = (texto: string) => Number(texto.replace(',', '.'))

export function sugerirValidade(base: string, dias: number | null | undefined): string {
  if (!base || dias == null) return ''
  const [ano, mes, dia] = base.split('-').map(Number)
  if (!ano || !mes || !dia) return ''
  return new Date(ano, mes - 1, dia + dias).toLocaleDateString('sv-SE')
}

export const sugerirValidadeDosGrupos = (grupos: Grupo[], dias: number | null | undefined) =>
  grupos.map((grupo) => grupo.validadeManual ? grupo : { ...grupo, validade: sugerirValidade(grupo.fabricacao, dias) })

export function gruposParaApi(grupos: Grupo[]): NovoItem[] {
  return grupos.map((grupo) => ({
    quantidade_unidades: Math.trunc(numeroDe(grupo.unidades)),
    quantidade: numeroDe(grupo.conteudo),
    fabricante: grupo.fabricante.trim() || null,
    data_fabricacao: grupo.fabricacao || null,
    data_validade: grupo.validade || null,
  }))
}

export function resumoDosGrupos(grupos: Grupo[]) {
  const unidadesDo = (grupo: Grupo) => Math.trunc(numeroDe(grupo.unidades)) || 0
  const unidades = grupos.reduce((total, grupo) => total + unidadesDo(grupo), 0)
  const quantidade = grupos.reduce((total, grupo) => total + unidadesDo(grupo) * (numeroDe(grupo.conteudo) || 0), 0)
  const validades = grupos.map((grupo) => grupo.validade).filter(Boolean).sort()
  return { unidades, quantidade, menorValidade: validades[0] ?? '' }
}
