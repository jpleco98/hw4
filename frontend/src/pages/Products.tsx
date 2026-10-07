import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getCategories, getProducts, type ProductSummary } from '../api'
import ProductCard from '../components/ProductCard'
import { ProductGridSkeleton } from '../components/Skeletons'
import { useChatResults, type ChatResults } from '../chatResults'
import DanAvatar from '../components/DanAvatar'

// "Chat view": the products Handsome Dan matched, rendered as normal product cards.
// They are the same <ProductCard> links as the catalogue grid, so clicking one opens the detail page.
function ChatResultsView({ results, onBrowseAll, onClear }: { results: ChatResults; onBrowseAll: () => void; onClear: () => void }) {
  const n = results.products.length
  return (
    <section className="section">
      <div className="chat-results-banner">
        <div>
          <span className="chat-results-eyebrow">
            <DanAvatar size={22} /> Picked for you by Handsome Dan
          </span>
          <h1>{results.title}</h1>
          <p>
            {n} item{n === 1 ? '' : 's'} matching “{results.query}”
            {results.size && (
              <>
                {' '}
                · stock shown for size <strong>{results.size}</strong>
              </>
            )}
          </p>
        </div>
        <div className="chat-results-actions">
          <button className="btn" onClick={onBrowseAll}>
            Browse all products
          </button>
          <button className="btn btn-ghost" onClick={onClear}>
            Clear results
          </button>
        </div>
      </div>
      {/* key forces a fresh fade-in whenever new results arrive */}
      <div className="product-grid chat-results-grid" key={results.receivedAt}>
        {results.products.map((p, i) => (
          <ProductCard
            key={p.product_id}
            product={p}
            focusSize={results.size}
            style={{ animationDelay: `${Math.min(i, 12) * 40}ms` }}
          />
        ))}
      </div>
    </section>
  )
}

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const q = params.get('q') ?? ''
  const view = params.get('view')
  const chatResults = useChatResults()

  const [categories, setCategories] = useState<string[]>([])
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(q)

  useEffect(() => {
    getCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    setProducts(null)
    setError('')
    getProducts({ q, category })
      .then(setProducts)
      .catch(() => setError("We couldn't load products. Make sure the backend is running on port 8000."))
  }, [q, category])

  function update(next: { q?: string; category?: string }) {
    const merged = { q, category, ...next }
    const p = new URLSearchParams()
    if (merged.q) p.set('q', merged.q)
    if (merged.category) p.set('category', merged.category)
    setParams(p)
  }

  if (view === 'chat' && chatResults.results) {
    return (
      <ChatResultsView
        results={chatResults.results}
        onBrowseAll={() => setParams({})}
        onClear={() => {
          chatResults.clear()
          setParams({})
        }}
      />
    )
  }

  return (
    <section className="section">
      {chatResults.results && (
        <button className="chat-results-return" onClick={() => setParams({ view: 'chat' })}>
          💬 Back to your chat results: <strong>{chatResults.results.title}</strong> ({chatResults.results.products.length})
        </button>
      )}
      <div className="section-head">
        <p className="eyebrow">The full collection</p>
        <h1>Shop Campus Customs</h1>
        <p>Every piece below is officially licensed Yale apparel, straight from our New Haven shop.</p>
      </div>

      <div className="toolbar">
        <form
          className="search"
          onSubmit={(e) => {
            e.preventDefault()
            update({ q: search.trim() })
          }}
        >
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, college, sport…"
            aria-label="Search products"
          />
          <button className="btn" type="submit">
            Search
          </button>
        </form>
        <div className="chips">
          <button className={`chip ${!category ? 'active' : ''}`} onClick={() => update({ category: '' })}>
            All
          </button>
          {categories.map((c) => (
            <button key={c} className={`chip ${category === c ? 'active' : ''}`} onClick={() => update({ category: c })}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="notice error">{error}</p>}
      {!error && products === null && <ProductGridSkeleton />}
      {products && (
        <>
          <p className="result-count">
            {products.length} item{products.length === 1 ? '' : 's'}
            {q && ` matching “${q}”`}
          </p>
          <div className="product-grid">
            {products.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
          {products.length === 0 && <p className="notice">No matches — try a different search or category.</p>}
        </>
      )}
    </section>
  )
}
