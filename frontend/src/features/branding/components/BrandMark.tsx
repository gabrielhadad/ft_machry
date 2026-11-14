import { useBranding } from '../hooks/useBranding'

type Variante = 'symbol' | 'horizontal' | 'print'

export function BrandMark({ className, variant = 'symbol' }: { className: string; variant?: Variante }) {
  const { logo, logo_horizontal, logo_impressao, sigla, nome } = useBranding()
  let source = logo
  if (variant === 'horizontal') source = logo_horizontal ?? logo
  if (variant === 'print') source = logo_impressao ?? logo
  return <div className={`${className}${source ? ' has-logo' : ''}`}>
    {source ? <img src={source} alt={nome} /> : sigla}
  </div>
}
