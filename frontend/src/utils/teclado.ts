import type { KeyboardEvent } from 'react'

export function ativarComTeclado(acao: () => void) {
  return (event: KeyboardEvent) => {
    if (event.key !== 'Enter' && event.key !== ' ') return
    event.preventDefault()
    acao()
  }
}
