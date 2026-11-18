import { useEffect, useRef, useState } from 'react'
import {
  alternarTimerGlobal,
  obterResponsavelGlobal,
  resetarTimerGlobal,
  useTodosTimersAtivos,
} from './timersStore'

function formatarTempo(totalSegundos: number): string {
  const minutos = Math.floor(totalSegundos / 60)
  const segundos = totalSegundos % 60
  return `${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`
}

export function ActiveTimersBadge() {
  const timers = useTodosTimersAtivos()
  const [aberto, setAberto] = useState(false)
  const [, setTick] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  const temRodando = timers.some((t) => t.inicioTimestamp !== null)

  useEffect(() => {
    if (!temRodando) return
    const intervalo = window.setInterval(() => setTick((t) => t + 1), 1000)
    return () => window.clearInterval(intervalo)
  }, [temRodando])

  useEffect(() => {
    if (!aberto) return
    function handleClickFora(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setAberto(false)
      }
    }
    document.addEventListener('mousedown', handleClickFora)
    return () => document.removeEventListener('mousedown', handleClickFora)
  }, [aberto])

  if (timers.length === 0) return null

  const qtdRodando = timers.filter((t) => t.inicioTimestamp !== null).length
  const algumEstourou = timers.some((t) => {
    const ms = t.acumuladoMs + (t.inicioTimestamp !== null ? Date.now() - t.inicioTimestamp : 0)
    return t.minutosPrevistos > 0 && Math.floor(ms / 1000) >= t.minutosPrevistos * 60
  })

  return (
    <div className="active-timers-wrapper no-print" ref={containerRef}>
      <button
        type="button"
        className={`active-timers-trigger ${algumEstourou ? 'has-overtime' : ''}`}
        onClick={() => setAberto((prev) => !prev)}
        title="Ver preparos em andamento"
      >
        <span className="active-timers-icon" aria-hidden="true">⏱</span>
        <span>
          {qtdRodando > 0
            ? `${qtdRodando} em preparo`
            : `${timers.length} pausado${timers.length > 1 ? 's' : ''}`}
        </span>
      </button>

      {aberto && (
        <div className="active-timers-popover" role="dialog" aria-label="Preparos em andamento">
          <div className="active-timers-header">
            <strong>Cronômetros da cozinha</strong>
            <span>{timers.length} ativo(s)</span>
          </div>

          <ul className="active-timers-list">
            {timers.map((timer) => {
              const rodando = timer.inicioTimestamp !== null
              const totalMs = timer.acumuladoMs + (timer.inicioTimestamp !== null ? Date.now() - timer.inicioTimestamp : 0)
              const segundos = Math.floor(totalMs / 1000)
              const estourou = timer.minutosPrevistos > 0 && segundos >= timer.minutosPrevistos * 60
              const responsavel = obterResponsavelGlobal(timer.id)

              return (
                <li key={timer.id} className={`active-timer-item ${estourou ? 'is-overtime' : ''}`}>
                  <div className="active-timer-info">
                    <span className="active-timer-product">{timer.produtoNome}</span>
                    <span className="active-timer-stage">
                      Etapa {timer.faseOrdem}: {timer.faseNome}
                    </span>
                    <span className="active-timer-assignee">
                      {responsavel ? `👤 ${responsavel}` : 'Sem responsável'}
                    </span>
                  </div>

                  <div className="active-timer-controls">
                    <span className="active-timer-clock">
                      {formatarTempo(segundos)}
                      <small> / {timer.minutosPrevistos}m</small>
                    </span>
                    <button
                      type="button"
                      className="active-timer-action"
                      onClick={() => alternarTimerGlobal(timer.id)}
                    >
                      {rodando ? 'Pause' : 'Retomar'}
                    </button>
                    {!rodando && (
                      <button
                        type="button"
                        className="active-timer-action"
                        title="Remover"
                        onClick={() => resetarTimerGlobal(timer.id)}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}