import { moeda } from '../../utils/formatacao'

interface MoneyInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
}

export function MoneyInput({ value, onChange, placeholder, required }: MoneyInputProps) {
  return <input
    type="text"
    inputMode="numeric"
    required={required}
    placeholder={placeholder}
    value={value === '' ? '' : moeda.format(Number(value))}
    onChange={(event) => {
      const digits = event.target.value.replace(/\D/g, '')
      onChange(digits ? (Number(digits) / 100).toFixed(2) : '')
    }}
  />
}
