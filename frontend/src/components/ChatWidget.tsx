import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, matchPath, useLocation, useNavigate } from 'react-router-dom'
import {
  clearChatHistory,
  formatPrice,
  getChatHistory,
  streamChat,
  type ChatTurn,
  type PageInfo,
  type ProductSummary,
  type Verification,
} from '../api'
import { useAuth } from '../auth'
import { CHAT_RESULTS_PATH, useChatResults } from '../chatResults'
import { CHAT_ASK_EVENT, CHAT_OPEN_EVENT, sizeStockLabel } from '../stock'
import DanAvatar from './DanAvatar'
import Markdown from './Markdown'

interface Message extends ChatTurn {
  products?: ProductSummary[]
  size?: string | null // size the shopper asked about
  pageCount?: number // how many cards this reply put on the page
  verification?: Verification | null
  status?: string // live tool status while the reply is streaming
  pending?: boolean
  error?: boolean
}

const HISTORY_SENT = 10 // recent turns sent as context for guests

function greeting(name?: string): Message {
  return {
    role: 'assistant',
    content: `Woof, hi${name ? ` ${name}` : ''}! I'm **Handsome Dan**, your Campus Customs personal shopper. Ask me about styles, sizes, prices or stock. I check live inventory before I answer.`,
  }
}

// One-tap starter questions, tailored to the page the shopper is on.
function startersFor(onProductPage: boolean): string[] {
  return onProductPage
    ? ['Which sizes are in stock?', 'Do you have this in another color?', 'What goes well with this?']
    : ['What hoodies do you have?', 'Gifts for my dad under $60', 'Anything for Saybrook College?']
}

const TIP_KEY = 'cc_dan_tip_seen'

// Problem 11 fix: when the shopper asked about a size, show stock FOR THAT SIZE (not the all-sizes total)
// and open the product page with that size pre-selected.
function ChatProducts({ products, size }: { products: ProductSummary[]; size?: string | null }) {
  return (
    <div className="chat-products">
      {products.map((p) => {
        const out = size ? !p.sizes.some((s) => s.size === size && s.quantity > 0) : p.total_stock <= 0
        return (
          <Link
            key={p.product_id}
            to={`/products/${p.product_id}${size ? `?size=${encodeURIComponent(size)}` : ''}`}
            className="chat-product"
          >
            <img src={p.image_url} alt="" loading="lazy" />
            <span className="chat-product-name">{p.name}</span>
            <span className="chat-product-meta">{formatPrice(p.price)}</span>
            <span className={`chat-product-stock${out ? ' out' : ''}`}>
              {size ? sizeStockLabel(p, size) : out ? 'Sold out' : `${p.total_stock} in stock (all sizes)`}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

// Usability improvement 3, made visible: the backend fact-checked the numbers in this reply.
function VerifiedBadge({ v }: { v: Verification }) {
  const parts = []
  if (v.prices_checked) parts.push(`${v.prices_checked} price${v.prices_checked === 1 ? '' : 's'}`)
  if (v.quantities_checked) parts.push(`${v.quantities_checked} stock number${v.quantities_checked === 1 ? '' : 's'}`)
  const detail = parts.length ? parts.join(' and ') : 'numbers'
  return (
    <span className="verified" title={`Checked ${detail} against the live store database before replying.`}>
      ✓ {v.corrected ? 'Corrected & verified' : 'Verified'} against live inventory
    </span>
  )
}

export default function ChatWidget() {
  const { user } = useAuth()
  const chatResults = useChatResults()
  const navigate = useNavigate()
  const location = useLocation()

  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([greeting()])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [announcement, setAnnouncement] = useState('') // for screen readers
  const [showTip, setShowTip] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const toggleRef = useRef<HTMLButtonElement>(null)

  // Page context for the agent: which product page is open, or which chat-result cards are on screen,
  // so "do you have this in pink?" or "which of these is cheapest?" can be resolved.
  function pageInfo(): PageInfo {
    const productId = matchPath('/products/:productId', location.pathname)?.params.productId ?? null
    const onResults = location.pathname === '/products' && new URLSearchParams(location.search).get('view') === 'chat'
    const results = onResults ? chatResults.results : null
    return {
      path: location.pathname,
      product_id: productId,
      results_product_ids: results ? results.products.map((p) => p.product_id) : [],
      results_title: results?.title ?? null,
    }
  }

  // Launcher speech tip: appears once per session after a few seconds, unless the chat was already opened.
  useEffect(() => {
    if (sessionStorage.getItem(TIP_KEY)) return
    const t = window.setTimeout(() => setShowTip(true), 3500)
    return () => window.clearTimeout(t)
  }, [])
  useEffect(() => {
    if (open) {
      setShowTip(false)
      sessionStorage.setItem(TIP_KEY, '1')
    }
  }, [open])
  const dismissTip = () => {
    setShowTip(false)
    sessionStorage.setItem(TIP_KEY, '1')
  }

  // Whenever the account changes, reset the chat; logged-in shoppers get their saved conversation back.
  useEffect(() => {
    setMessages([greeting(user?.first_name)])
    if (!user) return
    getChatHistory()
      .then(({ messages: saved }) => {
        if (saved.length) setMessages([greeting(user.first_name), ...saved])
      })
      .catch(() => undefined)
  }, [user])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, open])

  // Focus management: focus the input when the panel opens; Escape closes it. When it closes, focus goes
  // back to the chat button (after it re-renders: on phones it is hidden while the chat is full-screen).
  const wasOpen = useRef(false)
  useEffect(() => {
    if (!open) {
      if (wasOpen.current) toggleRef.current?.focus()
      return
    }
    wasOpen.current = true
    inputRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  // Replace the last (pending) assistant message.
  const updateLast = (patch: Partial<Message>) =>
    setMessages((m) => [...m.slice(0, -1), { ...m[m.length - 1], ...patch }])

  async function send(text: string) {
    text = text.trim()
    if (!text || busy) return
    const history: ChatTurn[] = messages
      .slice(1) // skip the local greeting
      .filter((m) => !m.error && !m.pending)
      .slice(-HISTORY_SENT)
      .map(({ role, content }) => ({ role, content }))
    setInput('')
    setMessages((m) => [
      ...m,
      { role: 'user', content: text },
      { role: 'assistant', content: '', pending: true, status: 'Dan is on it…' },
    ])
    setBusy(true)
    setAnnouncement('Handsome Dan is thinking…')
    try {
      const res = await streamChat(text, history, pageInfo(), (e) => {
        if (e.type === 'status') {
          updateLast({ status: e.text })
          setAnnouncement(e.text)
        } else if (e.type === 'delta') updateLast({ content: e.text })
        else if (e.type === 'reset') updateLast({ content: '' })
      })
      // API contract: `page` = matches to render on the website as full product cards.
      if (res.page && res.page.products.length) {
        chatResults.show({ ...res.page, query: text, size: res.size, receivedAt: Date.now() })
        navigate(CHAT_RESULTS_PATH)
      }
      updateLast({
        content: res.reply,
        products: res.products,
        size: res.size,
        pageCount: res.page?.products.length,
        verification: res.verification,
        pending: false,
        status: undefined,
      })
      setAnnouncement(`Handsome Dan: ${res.reply.replace(/\*\*/g, '')}`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Sorry, I couldn't reach the store server."
      updateLast({ content: msg, error: true, pending: false, status: undefined })
      setAnnouncement(msg)
    } finally {
      setBusy(false)
    }
  }

  // Let other parts of the site ask the assistant (e.g. "Ask for alternatives" on a sold-out size).
  const sendRef = useRef(send)
  sendRef.current = send
  const onAsk = useCallback((e: Event) => {
    setOpen(true)
    void sendRef.current((e as CustomEvent<string>).detail)
  }, [])
  useEffect(() => {
    const onOpen = () => setOpen(true)
    window.addEventListener(CHAT_ASK_EVENT, onAsk)
    window.addEventListener(CHAT_OPEN_EVENT, onOpen)
    return () => {
      window.removeEventListener(CHAT_ASK_EVENT, onAsk)
      window.removeEventListener(CHAT_OPEN_EVENT, onOpen)
    }
  }, [onAsk])

  const onProductPage = Boolean(matchPath('/products/:productId', location.pathname))
  const showStarters = !busy && messages.length === 1

  async function onClearHistory() {
    if (!window.confirm('Delete your saved chat history? This cannot be undone.')) return
    try {
      await clearChatHistory()
      setMessages([greeting(user?.first_name)])
      setAnnouncement('Chat history deleted.')
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: "Sorry, I couldn't clear your history.", error: true }])
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  return (
    <div className={`chat${open ? ' chat-open' : ''}`}>
      {/* Screen-reader announcements: status updates and the finished reply (not every streamed word). */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>
      {open && (
        <section id="chat-panel" className="chat-panel" role="dialog" aria-labelledby="chat-title">
          <header className="chat-header">
            <div className="chat-id">
              <DanAvatar size={44} />
              <div>
                <strong id="chat-title">Handsome Dan</strong>
                <small>{user ? `Online · chatting as ${user.first_name}, history saved` : 'Online · guest chat, log in to save it'}</small>
              </div>
            </div>
            <div className="chat-header-actions">
              {user && messages.length > 1 && (
                <button className="chat-clear" onClick={onClearHistory} title="Delete saved chat history">
                  Clear history
                </button>
              )}
              <button
                className="chat-close"
                onClick={() => setOpen(false)}
                aria-label="Close chat"
              >
                ×
              </button>
            </div>
          </header>
          <div className="chat-messages" role="log" aria-label="Conversation">
            {messages.map((m, i) => (
              <div key={i} className={`chat-turn chat-turn-${m.role}`}>
                {m.role === 'assistant' && <DanAvatar size={30} className="turn-avatar" />}
                {m.pending && !m.content ? (
                  <div className="bubble bubble-assistant typing-status">
                    <span className="typing" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </span>
                    <span className="status-text">{m.status}</span>
                  </div>
                ) : (
                  <div
                    className={`bubble bubble-${m.role}${m.error ? ' bubble-error' : ''}${m.pending ? ' bubble-streaming' : ''}`}
                  >
                    {m.role === 'assistant' ? <Markdown text={m.content} /> : m.content}
                  </div>
                )}
                {m.pending && m.content && m.status && <span className="stream-status">{m.status}</span>}
                {m.products && m.products.length > 0 && <ChatProducts products={m.products} size={m.size} />}
                {m.pageCount ? (
                  <Link to={CHAT_RESULTS_PATH} className="chat-page-link">
                    Showing {m.pageCount} item{m.pageCount === 1 ? '' : 's'} on the page →
                  </Link>
                ) : null}
                {m.verification && <VerifiedBadge v={m.verification} />}
              </div>
            ))}
            {showStarters && (
              <div className="chat-starters" aria-label="Suggested questions">
                {startersFor(onProductPage).map((q) => (
                  <button key={q} type="button" onClick={() => void send(q)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form className="chat-input" onSubmit={onSubmit}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. Do you have navy hoodies in M?"
              aria-label="Message Handsome Dan"
              maxLength={1000}
            />
            <button type="submit" className="btn" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      {showTip && !open && (
        <div className="chat-tip-wrap">
          <button className="chat-tip" onClick={() => setOpen(true)}>
            <strong>Need a size?</strong>
            Ask me, I check live stock. 🐾
          </button>
          <button className="chat-tip-close" onClick={dismissTip} aria-label="Dismiss tip">
            ×
          </button>
        </div>
      )}
      <button
        ref={toggleRef}
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Chat with Handsome Dan, our shopping assistant'}
        aria-expanded={open}
        aria-controls="chat-panel"
      >
        {open ? <span className="chat-toggle-close">×</span> : <DanAvatar size={58} />}
      </button>
    </div>
  )
}
