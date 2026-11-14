import { useCallback, useRef, useState } from 'react'
import { apiListAll } from '../services/api'
import type { FaseCatalogo, FichaTecnica, Localizacao, Lote, Produto, SolicitacaoProducao } from '../types'

export type Recurso = 'produtos' | 'fichas' | 'fases' | 'lotes' | 'localizacoes' | 'solicitacoes'

export type EstadoDoRecurso = 'vazio' | 'pronto' | 'desatualizado'

export interface Dados {
  produtos: Produto[]
  fichas: FichaTecnica[]
  fases: FaseCatalogo[]
  lotes: Lote[]
  localizacoes: Localizacao[]
  solicitacoes: SolicitacaoProducao[]
}

export const dadosVazios: Dados = {
  produtos: [],
  fichas: [],
  fases: [],
  lotes: [],
  localizacoes: [],
  solicitacoes: [],
}

const todosOsRecursos: Recurso[] = ['produtos', 'fichas', 'fases', 'lotes', 'localizacoes', 'solicitacoes']

const rotaDoRecurso: Record<Recurso, string> = {
  produtos: '/api/produtos',
  fichas: '/api/fichas-tecnicas',
  fases: '/api/fichas-tecnicas/fases',
  lotes: '/api/estoque/lotes',
  localizacoes: '/api/estoque/localizacoes',
  solicitacoes: '/api/producao/solicitacoes',
}

export type Mutacao = 'produto' | 'ficha' | 'estoque' | 'producao' | 'localizacao'

export const recursosAfetados: Record<Mutacao, Recurso[]> = {
  produto: ['produtos', 'fichas', 'lotes'],
  ficha: ['fichas', 'fases'],
  estoque: ['lotes'],
  producao: ['solicitacoes', 'lotes'],
  localizacao: ['localizacoes', 'lotes'],
}

function estadosIniciais(): Record<Recurso, EstadoDoRecurso> {
  return { produtos: 'vazio', fichas: 'vazio', fases: 'vazio', lotes: 'vazio', localizacoes: 'vazio', solicitacoes: 'vazio' }
}

function versoesZeradas(): Record<Recurso, number> {
  return { produtos: 0, fichas: 0, fases: 0, lotes: 0, localizacoes: 0, solicitacoes: 0 }
}

export function useDados() {
  const [dados, setDados] = useState<Dados>(dadosVazios)
  const [estado, setEstado] = useState<Record<Recurso, EstadoDoRecurso>>(estadosIniciais)
  const [atualizando, setAtualizando] = useState(false)
  const estadoAtual = useRef(estadosIniciais())
  const versoes = useRef(versoesZeradas())
  const emAndamento = useRef(new Map<Recurso, Promise<void>>())

  const definirEstado = useCallback((recurso: Recurso, valor: EstadoDoRecurso) => {
    estadoAtual.current = { ...estadoAtual.current, [recurso]: valor }
    setEstado(estadoAtual.current)
  }, [])

  const buscarUm = useCallback(async (recurso: Recurso) => {
    versoes.current[recurso] += 1
    const versaoDestaBusca = versoes.current[recurso]

    const lista = await apiListAll(rotaDoRecurso[recurso])

    const houveBuscaMaisRecente = versoes.current[recurso] !== versaoDestaBusca
    if (houveBuscaMaisRecente) return
    setDados((atuais) => ({ ...atuais, [recurso]: lista } as Dados))
    definirEstado(recurso, 'pronto')
  }, [definirEstado])

  const iniciarBusca = useCallback((recurso: Recurso) => {
    const busca = buscarUm(recurso).finally(() => {
      if (emAndamento.current.get(recurso) === busca) emAndamento.current.delete(recurso)
      setAtualizando(emAndamento.current.size > 0)
    })
    emAndamento.current.set(recurso, busca)
    setAtualizando(true)
    return busca
  }, [buscarUm])

  const garantir = useCallback(async (recursos: Recurso[]) => {
    const pendentes = recursos.filter((recurso) => estadoAtual.current[recurso] !== 'pronto')
    await Promise.all(pendentes.map((recurso) => emAndamento.current.get(recurso) ?? iniciarBusca(recurso)))
  }, [iniciarBusca])

  const recarregar = useCallback(async (recursos: Recurso[]) => {
    await Promise.all(recursos.map(iniciarBusca))
  }, [iniciarBusca])

  const marcarDesatualizados = useCallback((recursos: Recurso[]) => {
    for (const recurso of recursos) {
      versoes.current[recurso] += 1
      emAndamento.current.delete(recurso)
      if (estadoAtual.current[recurso] === 'pronto') definirEstado(recurso, 'desatualizado')
    }
    setAtualizando(emAndamento.current.size > 0)
  }, [definirEstado])

  const limpar = useCallback(() => {
    for (const recurso of todosOsRecursos) versoes.current[recurso] += 1
    emAndamento.current.clear()
    setAtualizando(false)
    setDados(dadosVazios)
    estadoAtual.current = estadosIniciais()
    setEstado(estadoAtual.current)
  }, [])

  return { dados, estado, atualizando, garantir, recarregar, marcarDesatualizados, limpar }
}
