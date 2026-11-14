export const EVENTO_SESSAO_EXPIRADA = 'machry:session-expired'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    })
  } catch {
    throw new Error('Não foi possível conectar à API Flask.')
  }

  const body = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && path !== '/api/auth/login') {
      window.dispatchEvent(new CustomEvent(EVENTO_SESSAO_EXPIRADA))
    }
    throw new ApiError(body?.erro || `Erro HTTP ${response.status}`, response.status)
  }
  return body as T
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  per_page: number
  total: number
  pages: number
}

const PAGINA_MAXIMA = 500

function urlDaPagina(path: string, page: number) {
  const url = new URL(path, window.location.origin)
  url.searchParams.set('page', String(page))
  url.searchParams.set('per_page', String(PAGINA_MAXIMA))
  return url.pathname + url.search
}

function paginaValida<T>(resposta: PaginatedResponse<T> | T[] | null, pageEsperada: number): resposta is PaginatedResponse<T> {
  if (!resposta || Array.isArray(resposta)) return false
  if (!Array.isArray(resposta.items)) return false
  return resposta.page === pageEsperada
}

export async function apiListAll<T>(path: string): Promise<T[]> {
  const primeira = await api<PaginatedResponse<T> | T[]>(urlDaPagina(path, 1))
  if (Array.isArray(primeira)) return primeira
  if (!paginaValida(primeira, 1) || !Number.isInteger(primeira.pages) || primeira.pages < 0) {
    throw new Error('Formato inválido na resposta paginada da API.')
  }
  if (primeira.pages <= 1) return primeira.items

  const numerosRestantes = Array.from({ length: primeira.pages - 1 }, (_, indice) => indice + 2)
  const restantes = await Promise.all(
    numerosRestantes.map((page) => api<PaginatedResponse<T> | T[]>(urlDaPagina(path, page))),
  )

  const linhas = [...primeira.items]
  restantes.forEach((resposta, indice) => {
    const page = numerosRestantes[indice]
    if (!paginaValida(resposta, page)) {
      throw new Error(`Resposta inválida ao consultar a página ${page}.`)
    }
    linhas.push(...resposta.items)
  })
  return linhas
}
