import { createContext, useContext, useState, type ReactNode } from 'react'
import type { PageResults } from './api'

// Holds the latest product matches the chat agent sent to the page, so any page can render them.
// Kept in sessionStorage so the results survive opening a product and coming back (or a reload).

const STORAGE_KEY = 'cc_chat_results'

// Where chat results are shown: the Products page in "chat" view.
export const CHAT_RESULTS_PATH = '/products?view=chat'

export interface ChatResults extends PageResults {
  query: string // the shopper message that produced these results
  size?: string | null // size the shopper asked about (cards highlight its stock)
  receivedAt: number
}

interface ChatResultsState {
  results: ChatResults | null
  show: (results: ChatResults) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

function load(): ChatResults | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as ChatResults) : null
  } catch {
    return null
  }
}

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(load)

  const value: ChatResultsState = {
    results,
    show: (r) => {
      setResults(r)
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(r))
    },
    clear: () => {
      setResults(null)
      sessionStorage.removeItem(STORAGE_KEY)
    },
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
