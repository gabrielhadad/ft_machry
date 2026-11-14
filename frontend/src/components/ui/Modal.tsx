import type { ReactNode } from 'react'
import { useTravarRolagemDaPagina } from '../../hooks/useTravarRolagemDaPagina'

interface ModalProps {
  title: string
  eyebrow?: string
  wide?: boolean
  className?: string
  titleAside?: ReactNode
  subtitle?: ReactNode
  children: ReactNode
  footer: ReactNode
  onClose: () => void
}

export function Modal({ title, eyebrow, wide, className = '', titleAside, subtitle, children, footer, onClose }: ModalProps) {
  useTravarRolagemDaPagina()
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className={`dialog modal-card ${wide ? 'wide' : ''} ${className}`} role="dialog" aria-modal="true" aria-label={title}>
      <div className="dialog-head">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <div className="dialog-title"><h2>{title}</h2>{titleAside}</div>
          {subtitle && <p className="dialog-subtitle">{subtitle}</p>}
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Fechar" type="button">×</button>
      </div>
      {children}
      <div className="dialog-actions">{footer}</div>
    </section>
  </div>
}
