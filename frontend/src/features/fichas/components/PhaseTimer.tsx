import { useEffect, useState } from 'react'
import { alternarTimerGlobal, resetarTimerGlobal, type TimerMetadata, useTimerGlobal } from './timersStore'

interface PhaseTimerProps extends TimerMetadata {
  timerId: string
}

function formatarTempo(totalSegundos: number): string {
  const minutos = Math.floor(totalSegundos / 60)
  const segundos = totalSegundos % 60
  return `${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`
}

export function PhaseTimer({
  timerId,
  fichaId,
  produtoNome,
  faseNome,
  faseOrdem,
  minutosPrevistos,
}: PhaseTimerProps) {
  const estado = useTimerGlobal(timerId)
  const [, setTick] = useState(0)

  const rodando = estado?.inicioTimestamp !== null && estado !== undefined
  const iniciado = estado?.iniciado ?? false

  useEffect(() => {
    if (!rodando) return
    const intervalo = window.setInterval(() => setTick((t) => t + 1), 1000)
    return () => window.clearInterval(intervalo)
  }, [rodando])

  if (minutosPrevistos <= 0) {
    return <small>{minutosPrevistos} min</small>
  }

  const totalMs = (estado?.acumuladoMs ?? 0) + (estado?.inicioTimestamp != null ? Date.now() - estado.inicioTimestamp : 0)
  const segundos = Math.floor(totalMs / 1000)
  const estourouTempo = iniciado && segundos >= minutosPrevistos * 60

  return (
    <small className={`phase-timer ${estourouTempo ? 'is-overtime' : ''} ${rodando ? 'is-running' : ''}`}>
      <span className="phase-timer-display">
        {iniciado ? `${formatarTempo(segundos)} / ${minutosPrevistos} min` : `${minutosPrevistos} min`}
      </span>
      <button
        type="button"
        className="phase-timer-btn"
        onClick={() =>
          alternarTimerGlobal(timerId, {
            fichaId,
            produtoNome,
            faseNome,
            faseOrdem,
            minutosPrevistos,
          })
        }
      >
        {rodando ? 'Pause' : 'Iniciar'}
      </button>
      {iniciado && !rodando && (
        <button
          type="button"
          className="phase-timer-btn"
          title="Zerar cronômetro"
          onClick={() => resetarTimerGlobal(timerId)}
        >
          ↺
        </button>
      )}
    </small>
  )
}