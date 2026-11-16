import { useCallback, useEffect, useState } from 'react'
import { EVENTO_SESSAO_EXPIRADA } from '../../../services/api'
import type { UsuarioLogado } from '../../../types'
import { buscarUsuarioLogado, sair } from '../api/authApi'

interface OpcoesDaSessao {
  aoEntrar: (usuario: UsuarioLogado) => void
  aoEncerrar: () => void
}

export function useSessao({ aoEntrar, aoEncerrar }: OpcoesDaSessao) {
  const [usuario, setUsuario] = useState<UsuarioLogado | null | undefined>(undefined)

  const iniciar = useCallback((logado: UsuarioLogado) => {
    setUsuario(logado)
    aoEntrar(logado)
  }, [aoEntrar])

  const encerrar = useCallback(() => {
    setUsuario(null)
    aoEncerrar()
  }, [aoEncerrar])

  useEffect(() => {
    buscarUsuarioLogado().then(iniciar).catch(() => setUsuario(null))
  }, [iniciar])

  useEffect(() => {
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, encerrar)
    return () => window.removeEventListener(EVENTO_SESSAO_EXPIRADA, encerrar)
  }, [encerrar])

  const logout = async () => {
    await sair().catch(() => undefined)
    encerrar()
  }

  return { usuario, iniciar, logout }
}
