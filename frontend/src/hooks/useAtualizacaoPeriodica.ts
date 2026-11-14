import { useEffect, useRef } from 'react'

export function useAtualizacaoPeriodica(atualizar: () => void, intervaloMs: number, ativo: boolean) {
  const atualizarMaisRecente = useRef(atualizar)

  useEffect(() => {
    atualizarMaisRecente.current = atualizar
  })

  useEffect(() => {
    if (!ativo) return
    const atualizarSeVisivel = () => {
      if (!document.hidden) atualizarMaisRecente.current()
    }
    const timer = window.setInterval(atualizarSeVisivel, intervaloMs)
    document.addEventListener('visibilitychange', atualizarSeVisivel)
    return () => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', atualizarSeVisivel)
    }
  }, [intervaloMs, ativo])
}
