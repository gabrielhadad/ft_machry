import { useSyncExternalStore } from 'react'
import { api } from '../../../services/api'

export interface TimerMetadata {
  fichaId: number
  produtoNome: string
  faseNome: string
  faseOrdem: number
  minutosPrevistos: number
}

export interface TimerState extends TimerMetadata {
  id: string
  acumuladoMs: number
  inicioTimestamp: number | null
  iniciado: boolean
}

const STORAGE_KEY_TIMERS = 'cozinha_plus_timers_v1'
const STORAGE_KEY_ASSIGNEES = 'cozinha_plus_assignees_v1'

const timers = new Map<string, TimerState>()
const responsaveis = new Map<string, string>()
const listeners = new Set<() => void>()
let snapshotCache: TimerState[] = []

try {
  const salvoTimers = localStorage.getItem(STORAGE_KEY_TIMERS)
  if (salvoTimers) {
    const lista: TimerState[] = JSON.parse(salvoTimers)
    for (const item of lista) timers.set(item.id, item)
  }
  const salvoResp = localStorage.getItem(STORAGE_KEY_ASSIGNEES)
  if (salvoResp) {
    const pares: [string, string][] = JSON.parse(salvoResp)
    for (const [k, v] of pares) responsaveis.set(k, v)
  }
} catch {
  // ignora erro de storage
}

function salvarStorage() {
  try {
    localStorage.setItem(STORAGE_KEY_TIMERS, JSON.stringify(Array.from(timers.values())))
    localStorage.setItem(STORAGE_KEY_ASSIGNEES, JSON.stringify(Array.from(responsaveis.entries())))
  } catch {
    // ignora
  }
}

function notificar() {
  snapshotCache = Array.from(timers.values()).filter((t) => t.iniciado)
  salvarStorage()
  listeners.forEach((listener) => listener())
}

notificar()

async function enviarParaFilaDeProducao(fichaId: number) {
  if (!fichaId || Number.isNaN(fichaId)) return
  try {
    const resposta = await api<any>('/api/producao/solicitacoes')
    const lista = Array.isArray(resposta)
      ? resposta
      : (resposta?.items ?? resposta?.itens ?? resposta?.dados ?? [])

    const jaNaFila = lista.find(
      (item: any) =>
        item.ficha_tecnica_id === fichaId &&
        ['ABERTA', 'EM_SEPARACAO', 'EM_PRODUCAO'].includes(item.status)
    )

    if (jaNaFila) {
      if (jaNaFila.status !== 'EM_PRODUCAO') {
        await api(`/api/producao/solicitacoes/${jaNaFila.id}/status`, {
          method: 'PUT',
          body: JSON.stringify({ status: 'EM_PRODUCAO' }),
        })
      }
      return
    }

    const criada = await api<{ id: number }>('/api/producao/solicitacoes', {
      method: 'POST',
      body: JSON.stringify({ ficha_tecnica_id: fichaId }),
    })

    if (criada?.id) {
      await api(`/api/producao/solicitacoes/${criada.id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'EM_PRODUCAO' }),
      })
    }
  } catch (erro) {
    console.error('Erro ao enviar preparo para a fila:', erro)
  }
}

export function alternarTimerGlobal(id: string, meta?: TimerMetadata) {
  const existente = timers.get(id)
  const agora = Date.now()

  if (existente && existente.inicioTimestamp !== null) {
    timers.set(id, {
      ...existente,
      acumuladoMs: existente.acumuladoMs + (agora - existente.inicioTimestamp),
      inicioTimestamp: null,
      iniciado: true,
    })
  } else {
    const fichaId = meta?.fichaId ?? existente?.fichaId ?? Number(id.split('-')[0])
    const base: TimerState = existente ?? {
      id,
      fichaId,
      produtoNome: meta?.produtoNome ?? 'Preparo',
      faseNome: meta?.faseNome ?? 'Etapa',
      faseOrdem: meta?.faseOrdem ?? 1,
      minutosPrevistos: meta?.minutosPrevistos ?? 0,
      acumuladoMs: 0,
      inicioTimestamp: null,
      iniciado: true,
    }

    timers.set(id, {
      ...base,
      ...(meta ?? {}),
      fichaId,
      inicioTimestamp: agora,
      iniciado: true,
    })

    void enviarParaFilaDeProducao(fichaId)
  }

  notificar()
}

export function resetarTimerGlobal(id: string) {
  timers.delete(id)
  notificar()
}

export function definirResponsavelGlobal(id: string, nome: string) {
  const limpo = nome.trim()
  if (limpo) {
    responsaveis.set(id, limpo)
  } else {
    responsaveis.delete(id)
  }
  notificar()
}

export function removerResponsavelGlobal(id: string) {
  responsaveis.delete(id)
  notificar()
}

export function obterResponsavelGlobal(id: string): string {
  return responsaveis.get(id) ?? ''
}

export function useResponsavelGlobal(id: string): string {
  return useSyncExternalStore(
    (callback) => {
      listeners.add(callback)
      return () => listeners.delete(callback)
    },
    () => responsaveis.get(id) ?? ''
  )
}

export function useTimerGlobal(id: string): TimerState | undefined {
  return useSyncExternalStore(
    (callback) => {
      listeners.add(callback)
      return () => listeners.delete(callback)
    },
    () => timers.get(id)
  )
}

export function useTodosTimersAtivos(): TimerState[] {
  return useSyncExternalStore(
    (callback) => {
      listeners.add(callback)
      return () => listeners.delete(callback)
    },
    () => snapshotCache
  )
}