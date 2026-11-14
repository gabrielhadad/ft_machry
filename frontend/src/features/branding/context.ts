import { createContext } from 'react'
import type { Branding } from './types'

export const brandingPadrao: Branding = {
  nome: 'Cozinha+',
  subtitulo: 'GESTÃO DE COZINHA',
  sigla: 'C+',
  titulo: 'Cozinha+ · Operação de cozinha',
}

export const BrandingContext = createContext<Branding>(brandingPadrao)

export const BrandingProvider = BrandingContext.Provider
