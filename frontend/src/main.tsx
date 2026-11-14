import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import { Providers } from './app/providers'
import { carregarBranding } from './features/branding'
import './styles/global.css'

void carregarBranding().then((branding) => createRoot(document.getElementById('app')!).render(
  <StrictMode>
    <Providers branding={branding}>
      <App />
    </Providers>
  </StrictMode>,
))
