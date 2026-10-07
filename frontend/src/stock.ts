// Shared stock rules so the cards, the size picker and the chat all speak the same language.
// LOW_STOCK matches the backend's LOW_STOCK_THRESHOLD in tools.py.
import type { ProductSummary, SizeStock } from './api'

export const LOW_STOCK = 3

export type StockLevel = 'in' | 'low' | 'out'

export function stockLevel(qty: number): StockLevel {
  if (qty <= 0) return 'out'
  return qty <= LOW_STOCK ? 'low' : 'in'
}

// Card label for one size, e.g. "L: 20 in stock" / "L: only 2 left" / "Sold out in L".
export function sizeStockLabel(p: ProductSummary, size: string): string {
  const s = p.sizes.find((x) => x.size === size)
  if (!s || s.quantity <= 0) return `Sold out in ${size}`
  return stockLevel(s.quantity) === 'low' ? `${size}: only ${s.quantity} left` : `${size}: ${s.quantity} in stock`
}

export function stockText(s: SizeStock): string {
  const level = stockLevel(s.quantity)
  if (level === 'out') return `Sold out in ${s.size}`
  if (level === 'low') return `Only ${s.quantity} left in ${s.size}, order soon`
  return `${s.quantity} in stock in ${s.size}`
}

export interface CardBadge {
  label: string
  kind: 'out' | 'low' | 'limited'
}

export const ALMOST_GONE = 20 // total units across all sizes

// One badge per card, only for genuinely urgent cases (a badge on every card would mean nothing);
// the size strip under the price shows the per-size detail for all cards.
export function cardBadge(p: ProductSummary): CardBadge | null {
  if (p.total_stock <= 0) return { label: 'Sold out', kind: 'out' }
  if (p.total_stock <= ALMOST_GONE) return { label: `Almost gone: ${p.total_stock} left`, kind: 'low' }
  const out = p.sizes.filter((s) => s.quantity <= 0)
  if (p.sizes.length && out.length * 2 >= p.sizes.length) return { label: 'Few sizes left', kind: 'limited' }
  return null
}

// Ask the chat assistant something from anywhere on the site (ChatWidget listens for this event).
export const CHAT_ASK_EVENT = 'cc-chat-ask'
export function askAssistant(text: string) {
  window.dispatchEvent(new CustomEvent(CHAT_ASK_EVENT, { detail: text }))
}

// Open the chat without sending anything (e.g. the "Ask Handsome Dan" buttons).
export const CHAT_OPEN_EVENT = 'cc-chat-open'
export function openAssistant() {
  window.dispatchEvent(new Event(CHAT_OPEN_EVENT))
}
