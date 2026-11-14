import { useEffect } from 'react'

const CLASSE_DE_TRAVA = 'modal-aberto'

let modaisAbertos = 0

export function useTravarRolagemDaPagina() {
  useEffect(() => {
    modaisAbertos += 1
    document.body.classList.add(CLASSE_DE_TRAVA)
    return () => {
      modaisAbertos -= 1
      if (modaisAbertos === 0) document.body.classList.remove(CLASSE_DE_TRAVA)
    }
  }, [])
}
