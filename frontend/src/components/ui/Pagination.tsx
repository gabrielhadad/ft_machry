interface PaginationProps {
  page: number
  perPage: number
  total: number
  label: string
  onChange: (page: number) => void
}

export function Pagination({ page, perPage, total, label, onChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / perPage))
  if (total <= perPage) return null
  return <nav className="catalog-pagination" aria-label={label}>
    <span>Mostrando {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} de {total}</span>
    <div>
      <button type="button" className="secondary" disabled={page === 1} onClick={() => onChange(Math.max(1, page - 1))}>Anterior</button>
      <span>Página {page} de {pages}</span>
      <button type="button" className="secondary" disabled={page === pages} onClick={() => onChange(Math.min(pages, page + 1))}>Próxima</button>
    </div>
  </nav>
}
