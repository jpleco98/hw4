import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, type ProductSummary } from '../api'
import { cardBadge, sizeStockLabel, stockLevel } from '../stock'

interface Props {
  product: ProductSummary
  style?: CSSProperties
  focusSize?: string | null // highlight this size's stock (chat results for "size L")
}

export default function ProductCard({ product, style, focusSize }: Props) {
  const badge = cardBadge(product)
  return (
    <Link
      to={`/products/${product.product_id}${focusSize ? `?size=${encodeURIComponent(focusSize)}` : ''}`}
      className="product-card"
      style={style}
    >
      <div className="product-card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {badge && <span className={`badge badge-${badge.kind}`}>{badge.label}</span>}
      </div>
      <div className="product-card-body">
        <span className="product-card-cat">{product.category}</span>
        <h3>{product.name}</h3>
        <p>{product.short_description}</p>
        <div className="product-card-foot">
          <span className="price">{formatPrice(product.price)}</span>
          {product.sizes.length > 0 && (
            <ul className="size-strip" aria-label="Sizes in stock">
              {product.sizes.map((s) => {
                const lv = stockLevel(s.quantity)
                return (
                  <li
                    key={s.size}
                    className={`size-dot size-dot-${lv}${s.size === focusSize ? ' size-dot-focus' : ''}`}
                    title={lv === 'out' ? `${s.size}: sold out` : `${s.size}: ${s.quantity} left`}
                    aria-label={lv === 'out' ? `${s.size} sold out` : `${s.size} available`}
                  >
                    {s.size}
                  </li>
                )
              })}
            </ul>
          )}
        </div>
        {focusSize && <span className="card-size-stock">{sizeStockLabel(product, focusSize)}</span>}
      </div>
    </Link>
  )
}
