import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ApiError, formatPrice, getProduct, type ProductDetail } from '../api'
import { CHAT_RESULTS_PATH, useChatResults } from '../chatResults'
import DanAvatar from '../components/DanAvatar'
import SizePicker from '../components/SizePicker'
import { askAssistant } from '../stock'
import { ProductDetailSkeleton } from '../components/Skeletons'

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [searchParams] = useSearchParams()
  const requestedSize = searchParams.get('size') // e.g. from a chat card for "size L"
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')
  const { results } = useChatResults()
  const fromChat = results?.products.some((p) => p.product_id === productId) ?? false

  useEffect(() => {
    setProduct(null)
    setError('')
    getProduct(productId)
      .then(setProduct)
      .catch((e) =>
        setError(e instanceof ApiError && e.status === 404 ? 'We could not find that product.' : 'Could not load this product.'),
      )
  }, [productId])

  if (error)
    return (
      <section className="section">
        <p className="notice error">{error}</p>
        <Link to="/products">← Back to all products</Link>
      </section>
    )
  if (!product) return <ProductDetailSkeleton />

  return (
    <section className="section">
      {fromChat ? (
        <Link to={CHAT_RESULTS_PATH} className="back-link">
          ← Back to your chat results ({results!.title})
        </Link>
      ) : (
        <Link to="/products" className="back-link">
          ← Back to all products
        </Link>
      )}
      <div className="product-detail">
        <div className="product-detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <span className="product-card-cat">{product.category}</span>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <p className="description">{product.description}</p>

          <dl className="facts">
            <dt>Style</dt>
            <dd>{product.garment_type}</dd>
            <dt>Colors</dt>
            <dd>{product.colors.join(', ')}</dd>
          </dl>

          <h2 className="h-small">Choose your size</h2>
          <SizePicker
            key={`${product.product_id}-${requestedSize ?? ''}`}
            productName={product.name}
            sizes={product.inventory}
            initialSize={requestedSize}
          />
          <p className="muted">{product.total_stock} units across all sizes. Stock is live from our New Haven shop.</p>

          <div className="pdp-dan">
            <DanAvatar size={46} />
            <p>
              <strong>Questions about fit or colors?</strong>
              <br />
              Handsome Dan checks live stock for you.
            </p>
            <button className="btn btn-ghost btn-small" onClick={() => askAssistant('Do you have this in another color?')}>
              Ask Dan
            </button>
          </div>

          <div className="tags">
            {product.search_tags.map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
