
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type ChangeEvent
} from 'react'

import type { Usuario, View } from './types'

const primaryNavigation: Array<[View, string, string]> = [
  ['inicio', '⌂', 'Visão geral'],
  ['produtos', '◫', 'Produtos'],
  ['fichas', '≡', 'Fichas técnicas'],
  ['estoque', '▦', 'Estoque'],
  ['producao', '◉', 'Produção'],
  ['historico', '↺', 'Movimentações'],
  ['locais', '▤', 'Localizações'],
  ['usuarios', '♙', 'Usuários'],
]

const titles: Record<View, string> = {
  inicio: 'Visão geral',
  produtos: 'Produtos',
  fichas: 'Fichas técnicas',
  estoque: 'Estoque',
  producao: 'Produção',
  historico: 'Movimentações',
  locais: 'Localizações',
  usuarios: 'Usuários',
}

export function Shell({
  view,
  menuOpen,
  apiOnline,
  usuario,
  onNavigate,
  onMenuToggle,
  onLogout,
  children
}: {
  view: View
  menuOpen: boolean
  apiOnline: boolean
  usuario: Usuario
  onNavigate: (view: View) => void
  onMenuToggle: () => void
  onLogout: () => void
  children: ReactNode
}) {
  const allowedViews: Record<Usuario['papel'], View[]> = {
    OWNER: [
      'inicio',
      'produtos',
      'fichas',
      'estoque',
      'producao',
      'historico',
      'locais',
      'usuarios'
    ],
    ADMIN: [
      'inicio',
      'fichas',
      'estoque',
      'producao',
      'historico',
      'locais'
    ],
    USER: ['fichas', 'producao'],
  }

  const visibleNavigation = primaryNavigation.filter(([target]) =>
    allowedViews[usuario.papel].includes(target)
  )

  const roleLabel = {
    OWNER: 'Proprietária',
    ADMIN: 'Gestor',
    USER: 'Cozinha'
  }[usuario.papel]

  const navButton = ([target, icon, label]: [View, string, string]) => (
    <button
      className={`nav ${view === target ? 'active' : ''}`}
      key={target}
      onClick={() => onNavigate(target)}
      type="button"
    >
      <span aria-hidden="true">{icon}</span>
      {label}
    </button>
  )

  return (
    <div className="layout">
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">C+</div>
          <div>
            <strong>Cozinha Mais</strong>
            <small>GESTÃO DE COZINHA</small>
          </div>
        </div>

        <p className="nav-caption">OPERAÇÃO</p>

        <nav>
          {visibleNavigation.map((item) => navButton(item))}
        </nav>

        <div className="account">
          <div className="account-avatar">
            {usuario.nome.charAt(0).toUpperCase()}
          </div>

          <div>
            <strong>{usuario.nome}</strong>
            <small>{roleLabel}</small>
          </div>

          <button onClick={onLogout} type="button">
            Sair
          </button>
        </div>

        <div className={`api-state ${apiOnline ? '' : 'offline'}`}>
          <i />
          <div>
            <strong>
              {apiOnline ? 'API conectada' : 'API indisponível'}
            </strong>
            <small>Flask · banco integrado</small>
          </div>
        </div>
      </aside>

      <main>
        <header>
          <button
            className="menu"
            onClick={onMenuToggle}
            aria-label="Abrir menu"
            type="button"
          >
            ☰
          </button>

          <div>
            <small>ÁREA ATUAL</small>
            <strong>{titles[view]}</strong>
          </div>
        </header>

        <div className="content">{children}</div>
      </main>

      {menuOpen && (
        <button
          className="sidebar-scrim"
          onClick={onMenuToggle}
          aria-label="Fechar menu"
          type="button"
        />
      )}
    </div>
  )
}

export function Metric({
  label,
  value,
  detail
}: {
  label: string
  value: ReactNode
  detail: string
}) {
  return (
    <article className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}

export function PageHeading({
  eyebrow,
  title,
  description,
  action
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  )
}

export function EmptyState({
  title,
  text
}: {
  title: string
  text: string
}) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  )
}

export function Pagination({
  page,
  perPage,
  total,
  label,
  onChange
}: {
  page: number
  perPage: number
  total: number
  label: string
  onChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / perPage))

  if (total <= perPage) return null

  return (
    <nav className="catalog-pagination" aria-label={label}>
      <span>
        Mostrando {(page - 1) * perPage + 1}–
        {Math.min(page * perPage, total)} de {total}
      </span>

      <div>
        <button
          type="button"
          className="secondary"
          disabled={page === 1}
          onClick={() => onChange(Math.max(1, page - 1))}
        >
          Anterior
        </button>

        <span>
          Página {page} de {pages}
        </span>

        <button
          type="button"
          className="secondary"
          disabled={page === pages}
          onClick={() => onChange(Math.min(pages, page + 1))}
        >
          Próxima
        </button>
      </div>
    </nav>
  )
}

export function Modal({
  title,
  eyebrow,
  wide,
  children,
  footer,
  onClose
}: {
  title: string
  eyebrow: string
  wide?: boolean
  children: ReactNode
  footer: ReactNode
  onClose: () => void
}) {
  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) =>
        event.target === event.currentTarget && onClose()
      }
    >
      <section
        className={`dialog modal-card ${wide ? 'wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="dialog-head">
          <div>
            <span className="eyebrow">{eyebrow}</span>
            <h2>{title}</h2>
          </div>

          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Fechar"
            type="button"
          >
            ×
          </button>
        </div>

        {children}

        <div className="dialog-actions">{footer}</div>
      </section>
    </div>
  )
}

export type SearchSelectOption<V extends string | number> = {
  value: V
  label: string
}

const SEARCH_SELECT_MAX_RESULTS = 50

export function SearchSelect<V extends string | number>({
  options,
  value,
  onChange,
  required,
  disabled,
  placeholder = 'Buscar',
  ariaLabel
}: {
  options: SearchSelectOption<V>[]
  value: V
  onChange: (value: NoInfer<V>) => void
  required?: boolean
  disabled?: boolean
  placeholder?: string
  ariaLabel?: string
}) {
  const listId = useId()

  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [position, setPosition] = useState<CSSProperties>({})

  const selected = options.find((option) => option.value === value)

  const empty = !selected || selected.value === ''

  const emptyOption = options.find((option) => option.value === '')

  const canClear = Boolean(
    selected && !empty && emptyOption && !required && !disabled
  )

  const filtered = useMemo(() => {
    const search = query.trim().toLocaleLowerCase('pt-BR')

    return search
      ? options.filter((option) =>
          option.label.toLocaleLowerCase('pt-BR').includes(search)
        )
      : options
  }, [options, query])

  const visibleOptions = filtered.slice(
    0,
    SEARCH_SELECT_MAX_RESULTS
  )

  const hasMoreResults =
    filtered.length > SEARCH_SELECT_MAX_RESULTS

  useEffect(() => {
    if (!open) return

    const place = () => {
      const rect = inputRef.current?.getBoundingClientRect()

      if (!rect) return

      setPosition({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
        maxHeight: Math.max(
          160,
          Math.min(320, window.innerHeight - rect.bottom - 12)
        )
      })
    }

    place()

    window.addEventListener('scroll', place, true)
    window.addEventListener('resize', place)

    return () => {
      window.removeEventListener('scroll', place, true)
      window.removeEventListener('resize', place)
    }
  }, [open])

  useEffect(() => {
    if (open) {
      listRef.current?.children[active]?.scrollIntoView({
        block: 'nearest'
      })
    }
  }, [active, open])

  const openList = () => {
    setOpen(true)

    const selectedIndex = visibleOptions.findIndex(
      (option) => option.value === value
    )

    setActive(selectedIndex >= 0 ? selectedIndex : 0)
  }

  const close = () => {
    setOpen(false)
    setQuery('')
  }

  const choose = (option: SearchSelectOption<V>) => {
    onChange(option.value)

    inputRef.current?.setCustomValidity('')

    close()
  }

  const clear = () => {
    if (canClear && emptyOption) {
      onChange(emptyOption.value)

      inputRef.current?.setCustomValidity('')

      close()
      inputRef.current?.focus()
    }
  }

  const onKeyDown = (
    event: KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()

      if (!open) {
        openList()
      } else if (visibleOptions.length) {
        setActive((index) =>
          Math.min(index + 1, visibleOptions.length - 1)
        )
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()

      if (visibleOptions.length) {
        setActive((index) => Math.max(index - 1, 0))
      }
    } else if (event.key === 'Enter' && open) {
      event.preventDefault()

      if (visibleOptions[active]) {
        choose(visibleOptions[active])
      }
    } else if (event.key === 'Escape' && open) {
      event.preventDefault()
      event.stopPropagation()

      close()
    }
  }

  return (
    <div className={`picker ${canClear ? 'has-clear' : ''}`}>
      <input
        ref={inputRef}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={
          open && visibleOptions[active]
            ? `${listId}-option-${active}`
            : undefined
        }
        aria-autocomplete="list"
        aria-label={ariaLabel}
        required={required && empty}
        disabled={disabled}
        placeholder={selected ? selected.label : placeholder}
        value={open ? query : empty ? '' : selected.label}
        onFocus={openList}
        onClick={() => {
          if (!open) openList()
        }}
        onBlur={close}
        onKeyDown={onKeyDown}
        onChange={(event) => {
          const nextQuery = event.target.value

          setQuery(nextQuery)
          setActive(0)
          setOpen(true)

          if (required && nextQuery.trim()) {
            inputRef.current?.setCustomValidity(
              'Selecione uma opção válida da lista.'
            )
          } else {
            inputRef.current?.setCustomValidity('')
          }
        }}
      />

      {canClear && (
        <button
          type="button"
          className="picker-clear"
          aria-label="Limpar seleção"
          title="Limpar seleção"
          onMouseDown={(event) => event.preventDefault()}
          onClick={clear}
        >
          ×
        </button>
      )}

      {open && (
        <div className="picker-dropdown" style={position}>
          <div className="picker-results" aria-live="polite">
            {hasMoreResults
              ? `Mostrando ${SEARCH_SELECT_MAX_RESULTS} de ${filtered.length} resultados. Digite para refinar a busca.`
              : `${filtered.length} ${
                  filtered.length === 1
                    ? 'resultado'
                    : 'resultados'
                }`}
          </div>

          <ul
            id={listId}
            role="listbox"
            className="picker-list"
            ref={listRef}
          >
            {visibleOptions.length ? (
              visibleOptions.map((option, index) => (
                <li
                  key={String(option.value)}
                  id={`${listId}-option-${index}`}
                  role="option"
                  aria-selected={option.value === value}
                  className={index === active ? 'active' : ''}
                  onMouseDown={(event) => {
                    event.preventDefault()
                    choose(option)
                  }}
                  onMouseEnter={() => setActive(index)}
                >
                  {option.label}
                </li>
              ))
            ) : (
              <li className="picker-empty">
                Nenhum resultado
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}

type MoneyInputProps = {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
}

export function MoneyInput({
  value,
  onChange,
  placeholder = 'R$ 0,00',
  disabled = false,
}: MoneyInputProps) {
  const formatCurrency = (numericValue: string) => {
    if (!numericValue || Number.isNaN(Number(numericValue))) {
      return ''
    }

    return Number(numericValue).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    })
  }

  const [displayValue, setDisplayValue] = useState(
    formatCurrency(value)
  )

  useEffect(() => {
    setDisplayValue(formatCurrency(value))
  }, [value])

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const digits = event.target.value.replace(/\D/g, '')

    if (!digits) {
      setDisplayValue('')
      onChange('')
      return
    }

    const numericValue = (Number(digits) / 100).toFixed(2)

    onChange(numericValue)
    setDisplayValue(formatCurrency(numericValue))
  }

  return (
    <input
      type="text"
      inputMode="numeric"
      value={displayValue}
      onChange={handleChange}
      placeholder={placeholder}
      disabled={disabled}
    />
  )
}
