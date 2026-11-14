import { useEffect, useId, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent } from 'react'
import { normalizeSearch } from '../../utils/texto'

export type SearchSelectOption<V extends string | number> = { value: V; label: string }

interface SearchSelectProps<V extends string | number> {
  options: SearchSelectOption<V>[]
  value: V
  onChange: (value: NoInfer<V>) => void
  required?: boolean
  disabled?: boolean
  placeholder?: string
  ariaLabel?: string
}

export function SearchSelect<V extends string | number>({ options, value, onChange, required, disabled, placeholder = 'Buscar', ariaLabel }: SearchSelectProps<V>) {
  const listId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [position, setPosition] = useState<CSSProperties>({})
  const selected = options.find((option) => option.value === value)
  const empty = !selected || selected.value === ''
  const filtered = useMemo(() => {
    const search = normalizeSearch(query)
    return search ? options.filter((option) => normalizeSearch(option.label).includes(search)) : options
  }, [options, query])

  useEffect(() => {
    if (!open) return
    const place = () => {
      const rect = inputRef.current?.getBoundingClientRect()
      if (!rect) return
      setPosition({ top: rect.bottom + 4, left: rect.left, width: rect.width, maxHeight: Math.max(160, Math.min(320, window.innerHeight - rect.bottom - 12)) })
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
    if (open) listRef.current?.children[active]?.scrollIntoView({ block: 'nearest' })
  }, [active, open])

  const openList = () => {
    setOpen(true)
    setActive(Math.max(0, filtered.findIndex((option) => option.value === value)))
  }
  const close = () => {
    setOpen(false)
    setQuery('')
  }
  const choose = (option: SearchSelectOption<V>) => {
    onChange(option.value)
    close()
  }
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (!open) openList()
      else setActive((index) => Math.min(index + 1, filtered.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Enter' && open) {
      event.preventDefault()
      if (filtered[active]) choose(filtered[active])
    } else if (event.key === 'Escape' && open) {
      event.preventDefault()
      event.stopPropagation()
      close()
    }
  }

  return <div className="picker">
    <input
      ref={inputRef}
      role="combobox"
      aria-expanded={open}
      aria-controls={listId}
      aria-autocomplete="list"
      aria-label={ariaLabel}
      required={required}
      disabled={disabled}
      placeholder={selected ? selected.label : placeholder}
      value={open ? query : (empty ? '' : selected.label)}
      onFocus={openList}
      onClick={() => { if (!open) openList() }}
      onBlur={close}
      onKeyDown={onKeyDown}
      onChange={(event) => { setQuery(event.target.value); setActive(0); setOpen(true) }}
    />
    {open && <ul id={listId} role="listbox" className="picker-list" ref={listRef} style={position}>
      {filtered.length
        ? filtered.map((option, index) => <li
          key={String(option.value)}
          role="option"
          aria-selected={option.value === value}
          className={index === active ? 'active' : ''}
          onMouseDown={(event) => { event.preventDefault(); choose(option) }}
          onMouseEnter={() => setActive(index)}
        >{option.label}</li>)
        : <li className="picker-empty">Nenhum resultado</li>}
    </ul>}
  </div>
}
