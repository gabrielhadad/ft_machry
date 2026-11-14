export function RotuloDoCampo({ texto, opcional }: { texto: string; opcional?: boolean }) {
  return <span className="field-title">
    {texto}
    {opcional && <small className="optional"> (opcional)</small>}
  </span>
}
