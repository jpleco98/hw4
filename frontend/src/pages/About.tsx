import { Link } from 'react-router-dom'
import { PHOTOS, PhotoCredit } from '../photos'
import { openAssistant } from '../stock'
import { useReveal } from '../useReveal'

export default function About() {
  useReveal()
  return (
    <>
      <section className="hero">
        <img className="hero-img" src={PHOTOS.gate.src} alt={PHOTOS.gate.alt} />
        <div className="hero-inner">
          <p className="eyebrow">About Campus Customs</p>
          <h1>
            Blue and white, <em>stitched into New Haven.</em>
          </h1>
        </div>
        <PhotoCredit photo={PHOTOS.gate} />
      </section>

      <section className="section about">
        <div className="about-text" data-reveal>
          <p className="lede">
            Campus Customs runs Yale Bulldog Blue, an officially licensed shop for Yale University apparel, a short walk
            from Old Campus on Broadway.
          </p>

          <h2>Who we are</h2>
          <p>
            Our storefront is where students, visiting families and alumni stop in for a sweatshirt and leave with a
            little extra Bulldog pride. Online, we bring that same counter to wherever you are.
          </p>

          <h2>What we make</h2>
          <p>
            We think school spirit should be comfortable. That's why our shelves are full of soft hoodies, sturdy
            crewnecks, game-day tees and polished quarter-zips: the kind of pieces you'll actually reach for on a cold
            morning walk to class or a Saturday at the Bowl.
          </p>
          <p>
            Yale is many communities at once, and our collections reflect that. You'll find gear for every residential
            college, for the graduate and professional schools, for varsity teams from squash to sailing, and for the
            people cheering from the stands: moms, dads, grandparents, siblings and cousins.
          </p>

          <h2>How we help</h2>
          <p>
            Whether you're shopping in person or online, finding the right piece should be easy. Our chat assistant,
            Handsome Dan, points you to matching items and gives straight answers on price, sizes and what's in stock.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn">
              Start shopping
            </Link>
            <button className="btn btn-ghost" onClick={openAssistant}>
              Ask Handsome Dan
            </button>
          </div>
        </div>

        <aside className="about-card" data-reveal>
          <h3>Visit the shop</h3>
          <p>
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
          <h3>Officially licensed</h3>
          <p>Every item we carry is authorized Yale University merchandise.</p>
          <h3>For the whole family</h3>
          <p>Students, alumni, parents and fans: there's a Bulldog fit for everyone.</p>
        </aside>
      </section>
    </>
  )
}
