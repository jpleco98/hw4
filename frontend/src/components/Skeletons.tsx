// Loading placeholders shaped like the real content, so the page doesn't jump when data arrives.

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="product-grid" aria-busy="true" aria-label="Loading products">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="product-card skeleton-card" aria-hidden="true">
          <div className="skeleton skeleton-img" />
          <div className="product-card-body">
            <div className="skeleton skeleton-line short" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line short" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function ProductDetailSkeleton() {
  return (
    <section className="section" aria-busy="true" aria-label="Loading product">
      <div className="product-detail" aria-hidden="true">
        <div className="product-detail-img">
          <div className="skeleton skeleton-img" />
        </div>
        <div className="product-detail-info">
          <div className="skeleton skeleton-line short" />
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-line short" />
          <div className="skeleton skeleton-line" />
          <div className="skeleton skeleton-line" />
          <div className="size-options">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="skeleton skeleton-size" />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
