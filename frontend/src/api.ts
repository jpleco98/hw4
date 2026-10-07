// Typed client for the FastAPI backend. Shapes mirror backend/models.py.

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  category: string
  short_description: string
  colors: string[]
  price: number
  image_url: string
  total_stock: number
  sizes: SizeStock[]
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  inventory: SizeStock[]
}

// Matches the agent put on the page (Problem 7). Every card field comes from the DB, not the model.
export interface PageResults {
  title: string
  products: ProductSummary[]
}

// Fact-check summary from the backend's output validator (usability improvement 3).
export interface Verification {
  prices_checked: number
  quantities_checked: number
  corrected: boolean
}

export interface ChatReply {
  reply: string
  products: ProductSummary[]
  page: PageResults | null
  verification: Verification | null
  size: string | null // size the shopper asked about: cards show stock for this size
}

// Events from POST /api/chat/stream (usability improvement 4), one JSON object per line.
export type ChatStreamEvent =
  | { type: 'status'; text: string }
  | { type: 'delta'; text: string }
  | { type: 'reset' }
  | { type: 'done'; reply: ChatReply }
  | { type: 'error'; message: string }

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

export interface SignupInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI errors come back as {detail: string} or {detail: [{msg}...]} for validation errors.
function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  return fallback
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: 'same-origin', ...init })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, errorMessage(body, `${res.status} ${res.statusText}`))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

const postJson = <T>(url: string, data: unknown) =>
  request<T>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })

export const signup = (input: SignupInput) => postJson<User>('/api/auth/signup', input)
export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })
export const logout = () => request<void>('/api/auth/logout', { method: 'POST' })
export const getMe = () => request<User>('/api/auth/me')

export function getProducts(params: { q?: string; category?: string } = {}) {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.category) qs.set('category', params.category)
  const suffix = qs.toString() ? `?${qs}` : ''
  return request<ProductSummary[]>(`/api/products${suffix}`)
}

export const getCategories = () => request<string[]>('/api/categories')

export const getProduct = (id: string) => request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatHistoryItem extends ChatTurn {
  products: ProductSummary[]
  created_at: string
}

// What the shopper is looking at, sent with every chat message (backend re-validates it against the DB).
export interface PageInfo {
  path: string
  product_id: string | null
  results_product_ids: string[]
  results_title: string | null
}

export const sendChat = (message: string, history: ChatTurn[], page: PageInfo) =>
  postJson<ChatReply>('/api/chat', { message, history, page })

// Streams a chat reply: calls onEvent for every NDJSON line and resolves with the final ChatReply.
export async function streamChat(
  message: string,
  history: ChatTurn[],
  page: PageInfo,
  onEvent: (e: ChatStreamEvent) => void,
): Promise<ChatReply> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, errorMessage(body, "Sorry, I couldn't reach the store server."))
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let final: ChatReply | null = null
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let nl: number
    while ((nl = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, nl).trim()
      buffer = buffer.slice(nl + 1)
      if (!line) continue
      const event = JSON.parse(line) as ChatStreamEvent
      if (event.type === 'error') throw new ApiError(502, event.message)
      if (event.type === 'done') final = event.reply
      onEvent(event)
    }
  }
  if (!final) throw new ApiError(502, 'The reply was cut off. Please try again.')
  return final
}

export const clearChatHistory = () => request<void>('/api/chat/history', { method: 'DELETE' })

export const getChatHistory = () => request<{ messages: ChatHistoryItem[] }>('/api/chat/history')

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
