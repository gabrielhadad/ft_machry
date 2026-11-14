import type { ReactNode } from 'react'
import { BrandingProvider, type Branding } from '../features/branding'

export function Providers({ branding, children }: { branding: Branding; children: ReactNode }) {
  return <BrandingProvider value={branding}>{children}</BrandingProvider>
}
