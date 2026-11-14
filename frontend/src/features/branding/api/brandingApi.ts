import { brandingPadrao } from '../context'
import type { Branding } from '../types'

const TEMPO_LIMITE_MS = 3000

async function buscarBrandingPersonalizado(): Promise<Partial<Branding>> {
  try {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), TEMPO_LIMITE_MS)
    const response = await fetch('/api/branding', { signal: controller.signal })
    window.clearTimeout(timeout)
    if (response.ok) return await response.json()
  } catch {
    return {}
  }
  return {}
}

function aplicarNoDocumento(branding: Branding) {
  document.title = branding.titulo
  document.documentElement.style.setProperty('--brand-sigla', JSON.stringify(branding.sigla))
  if (branding.favicon) {
    document.querySelectorAll('link[rel="icon"]').forEach((link) => link.remove())
    document.head.append(Object.assign(document.createElement('link'), { rel: 'icon', href: branding.favicon }))
  }
  if (branding.apple_touch_icon) {
    document.querySelector<HTMLLinkElement>('link[rel="apple-touch-icon"]')?.setAttribute('href', branding.apple_touch_icon)
  }
  if (branding.css) {
    document.head.append(Object.assign(document.createElement('link'), { rel: 'stylesheet', href: branding.css }))
  }
}

export async function carregarBranding(): Promise<Branding> {
  const branding = { ...brandingPadrao, ...(await buscarBrandingPersonalizado()) }
  aplicarNoDocumento(branding)
  return branding
}
