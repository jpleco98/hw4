import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProducts, type ProductSummary } from '../api'
import DanAvatar from '../components/DanAvatar'
import ProductCard from '../components/ProductCard'
import { PHOTOS, PhotoCredit } from '../photos'
import { askAssistant, openAssistant } from '../stock'
import { useReveal } from '../useReveal'

// Editorial home page (Problem 10): lead with a big campus image and a story, *then* the storefront,
// the way premium apparel brands open their sites.

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  'champion-reverse-weave-crewneck',
  '2025-yale-vs-harvard-t-shirt',
  'yale-dad-hoodie',
]

const EDIT = [
  {
    eyebrow: 'The Hoodie Edit',
    title: 'Heavyweight warmth for New Haven winters',
    category: 'Hoodies',
    img: '/media/products/champion-reverse-weave-hoodie-1.jpg', // white background: blends into the tile
  },
  {
    eyebrow: 'Crewneck Classics',
    title: 'College crests & team names',
    category: 'Crewnecks',
    img: '/media/products/saybrook-college-crewneck.jpg',
  },
  {
    eyebrow: 'Game Day',
    title: 'Tees for the Bowl',
    category: 'T-Shirts',
    img: '/media/products/2025-yale-vs-harvard-t-shirt.jpg',
  },
]

const RIBBON = ['Boola Boola', 'Officially licensed Yale apparel', '57 Broadway, New Haven', 'Lux et Veritas', 'For Bulldogs since 1701']

const DAN_PROMPTS = ['What hoodies do you have?', 'Gifts for my dad under $60', 'Anything for Saybrook College?']

export default function Home() {
  const [featured, setFeatured] = useState<ProductSummary[]>([])

  useEffect(() => {
    getProducts()
      .then((all) => {
        const picks = FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter(
          (p): p is ProductSummary => Boolean(p),
        )
        setFeatured(picks.length ? picks : all.slice(0, 4))
      })
      .catch(() => setFeatured([]))
  }, [])

  useReveal([featured.length])

  return (
    <>
      {/* 1. Full-bleed hero: image first, storefront later */}
      <section className="home-hero" aria-label="Welcome">
        <img className="home-hero-img" src={PHOTOS.hero.src} alt={PHOTOS.hero.alt} fetchPriority="high" />
        <div className="home-hero-content">
          <p className="eyebrow">Est. New Haven · Officially licensed</p>
          <h1>
            Wear the <em>Blue.</em>
          </h1>
          <p className="home-hero-sub">
            Heavyweight hoodies, college crests and game-day classics for every Bulldog: students, alumni and the
            proudest parents in the stands.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">
              Shop the collection
            </Link>
            <button className="btn btn-outline-light" onClick={openAssistant}>
              <DanAvatar size={26} /> Ask Handsome Dan
            </button>
          </div>
        </div>
        <a className="scroll-cue" href="#the-edit">
          Scroll
        </a>
        <PhotoCredit photo={PHOTOS.hero} />
      </section>

      {/* 2. Varsity marquee ribbon */}
      <div className="ribbon" aria-hidden="true">
        <div className="ribbon-track">
          {[...RIBBON, ...RIBBON, ...RIBBON, ...RIBBON].map((t, i) => (
            <span key={i}>{t}</span>
          ))}
        </div>
      </div>

      {/* 3. The Edit: three big category stories */}
      <section className="section" id="the-edit">
        <div className="section-head section-head-row" data-reveal>
          <div>
            <p className="eyebrow">The Edit</p>
            <h2>Find your Yale uniform</h2>
          </div>
          <Link to="/products" className="link-arrow">
            Shop everything →
          </Link>
        </div>
        <div className="edit-grid">
          {EDIT.map((e, i) => (
            <Link
              key={e.category}
              to={`/products?category=${encodeURIComponent(e.category)}`}
              className="edit-tile"
              data-reveal
              style={{ transitionDelay: `${i * 90}ms` }}
            >
              <img src={e.img} alt="" loading="lazy" />
              <p className="eyebrow">{e.eyebrow}</p>
              <h3>{e.title}</h3>
              <span className="link-arrow">Shop {e.category} →</span>
            </Link>
          ))}
        </div>
      </section>

      {/* 4. Editorial split: campus life */}
      <section className="split" aria-label="Life on Old Campus">
        <div className="split-media">
          <img src={PHOTOS.oldCampus.src} alt={PHOTOS.oldCampus.alt} loading="lazy" />
          <PhotoCredit photo={PHOTOS.oldCampus} />
        </div>
        <div className="split-copy" data-reveal>
          <p className="eyebrow">Life on Old Campus</p>
          <h2>
            Made for the walk <em>to class.</em>
          </h2>
          <p>
            From the first crisp morning on Old Campus to the last lap of finals, our crewnecks and quarter-zips
            are the layers Yale actually lives in. Soft inside, built to last four years (and every reunion after).
          </p>
          <Link to="/products?category=Crewnecks" className="btn">
            Shop crewnecks
          </Link>
        </div>
      </section>

      {/* 5. Bestsellers */}
      <section className="section">
        <div className="section-head section-head-row" data-reveal>
          <div>
            <p className="eyebrow">Bulldog favorites</p>
            <h2>What everyone's wearing</h2>
          </div>
          <Link to="/products" className="link-arrow">
            View all 102 →
          </Link>
        </div>
        <div className="product-grid" data-reveal>
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      {/* 6. Meet Handsome Dan */}
      <section className="dan-band" aria-label="Meet Handsome Dan">
        <div className="dan-band-inner" data-reveal>
          <DanAvatar size={170} />
          <div>
            <p className="eyebrow">Your personal shopper</p>
            <h2>Meet Handsome Dan.</h2>
            <p>
              Named after Yale's famous bulldog, Dan knows every hoodie on our shelves. Ask him what's in your size,
              what's almost gone, or what to get your roommate. He checks live inventory before he answers.
            </p>
            <div className="dan-prompts">
              {DAN_PROMPTS.map((q) => (
                <button key={q} onClick={() => askAssistant(q)}>
                  “{q}”
                </button>
              ))}
            </div>
            <button className="btn btn-light" onClick={openAssistant}>
              Chat with Dan
            </button>
          </div>
        </div>
      </section>

      {/* 7. Visit the shop */}
      <section className="visit" aria-label="Visit the shop">
        <img src={PHOTOS.street.src} alt={PHOTOS.street.alt} loading="lazy" />
        <div className="visit-card" data-reveal>
          <p className="eyebrow">Visit the shop</p>
          <h2>Steps from Old Campus.</h2>
          <p className="visit-address">57 Broadway, New Haven, CT 06511</p>
          <p>Try it on in person, or shop online and let Dan help you find your size first.</p>
          <Link to="/about" className="btn">
            Our story
          </Link>
        </div>
        <PhotoCredit photo={PHOTOS.street} />
      </section>
    </>
  )
}
