export const DIA_MS = 86400000

export const hojeIso = () => new Date().toLocaleDateString('sv-SE')

export function paraData(valor: string | null) {
  if (!valor) return null
  const data = new Date(valor.length === 10 ? `${valor}T12:00:00` : valor.replace(' ', 'T'))
  return Number.isNaN(data.getTime()) ? null : data
}

export const formatarData = (valor: string | null) => paraData(valor)?.toLocaleDateString('pt-BR') ?? '—'

export const formatarDiaMes = (valor: string | null) =>
  paraData(valor)?.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) ?? '—'

export const formatarDataHora = (valor: string) => paraData(valor)?.toLocaleString('pt-BR') ?? valor

export const inicioDoDia = (data: Date) => new Date(data.getFullYear(), data.getMonth(), data.getDate()).getTime()

export function diasAte(valor: string | null) {
  const data = paraData(valor)
  return data ? Math.round((inicioDoDia(data) - inicioDoDia(new Date())) / DIA_MS) : null
}
