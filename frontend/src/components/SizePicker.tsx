import { useState } from 'react'
import type { SizeStock } from '../api'
import { askAssistant, stockLevel, stockText } from '../stock'

// Size buttons with live availability. Sold-out sizes stay clickable (so shoppers learn *why*),
// but are struck through, and offer a one-click "find alternatives" question to the assistant.
interface Props {
  productName: string
  sizes: SizeStock[]
  initialSize?: string | null // pre-select the size the shopper asked about in chat
}

export default function SizePicker({ productName, sizes, initialSize }: Props) {
  const firstInStock = sizes.find((s) => s.quantity > 0)?.size ?? null
  const start = initialSize && sizes.some((s) => s.size === initialSize) ? initialSize : firstInStock
  const [selected, setSelected] = useState<string | null>(start)
  const current = sizes.find((s) => s.size === selected) ?? null
  const level = current ? stockLevel(current.quantity) : null

  return (
    <div className="size-picker">
      <div className="size-options" role="radiogroup" aria-label="Choose a size">
        {sizes.map((s) => {
          const lv = stockLevel(s.quantity)
          return (
            <button
              key={s.size}
              type="button"
              role="radio"
              aria-checked={selected === s.size}
              aria-label={`${s.size}: ${lv === 'out' ? 'sold out' : `${s.quantity} in stock`}`}
              className={`size-option size-${lv}${selected === s.size ? ' selected' : ''}`}
              onClick={() => setSelected(s.size)}
            >
              <span className="size-label">{s.size}</span>
              <span className="size-sub">{lv === 'out' ? 'Sold out' : lv === 'low' ? `${s.quantity} left` : 'In stock'}</span>
            </button>
          )
        })}
      </div>
      <p className={`size-status size-status-${level ?? 'none'}`} aria-live="polite">
        {current ? stockText(current) : 'This item is currently sold out in every size.'}
      </p>
      {(level === 'out' || !current) && (
        <button
          type="button"
          className="btn btn-ghost btn-small"
          onClick={() =>
            askAssistant(
              current
                ? `The ${productName} is sold out in ${current.size}. What similar items do you have in ${current.size}?`
                : `The ${productName} is sold out. What similar items are in stock?`,
            )
          }
        >
          💬 Ask the assistant for alternatives
        </button>
      )}
    </div>
  )
}
