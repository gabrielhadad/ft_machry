import type { ReactNode } from 'react'

interface PageHeadingProps {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}

export function PageHeading({ eyebrow, title, description, action }: PageHeadingProps) {
  return <div className="page-heading">
    <div>
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
    {action}
  </div>
}
