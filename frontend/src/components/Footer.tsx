import { Link } from 'react-router-dom'
import { PHOTOS } from '../photos'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div>
          <p className="footer-brand">Campus Customs</p>
          <p>Officially licensed Yale apparel, for every Bulldog.</p>
          <p>57 Broadway, New Haven, CT 06511</p>
        </div>
        <div>
          <h4>Shop</h4>
          <nav className="footer-links" aria-label="Shop">
            <Link to="/products?category=Hoodies">Hoodies</Link>
            <Link to="/products?category=Crewnecks">Crewnecks</Link>
            <Link to="/products?category=T-Shirts">T-Shirts</Link>
            <Link to="/products">All products</Link>
          </nav>
        </div>
        <div>
          <h4>Campus Customs</h4>
          <nav className="footer-links" aria-label="Company">
            <Link to="/about">About us</Link>
            <Link to="/signup">Create an account</Link>
            <Link to="/login">Log in</Link>
          </nav>
        </div>
      </div>
      <details className="footer-credits">
        <summary>Photo credits</summary>
        <ul>
          {Object.values(PHOTOS).map((p) => (
            <li key={p.src}>
              <a href={p.source} target="_blank" rel="noreferrer">
                {p.alt}
              </a>{' '}
              by {p.author}, licensed{' '}
              <a href={p.licenseUrl} target="_blank" rel="noreferrer">
                {p.license}
              </a>{' '}
              via Wikimedia Commons (resized).
            </li>
          ))}
        </ul>
      </details>
      <p className="footer-fine">© {new Date().getFullYear()} Campus Customs. Built for AI Foundations HW 4.</p>
    </footer>
  )
}
