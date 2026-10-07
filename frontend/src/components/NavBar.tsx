import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const overlay = location.pathname === '/' // transparent nav over the home hero photo

  // Close the mobile menu whenever the page changes.
  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname, location.search])

  // On the home page the nav turns solid once you scroll past the top of the hero.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const cls = ({ isActive }: { isActive: boolean }) => (isActive ? 'nav-link active' : 'nav-link')
  return (
    <header className={`navbar${overlay ? ' overlay' : ''}${scrolled ? ' scrolled' : ''}`}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      {!overlay && (
        <p className="announce">
          Officially licensed Yale apparel · <strong>Visit us at 57 Broadway, New Haven</strong>
        </p>
      )}
      <div className="navbar-inner">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <span className="brand-mark" aria-hidden="true">
            Y
          </span>
          <span>
            <strong>Campus Customs</strong>
            <small>Yale Bulldog Blue</small>
          </span>
        </Link>
        <button
          className="menu-toggle"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          aria-controls="site-menu"
          onClick={() => setMenuOpen((o) => !o)}
        >
          <span aria-hidden="true">{menuOpen ? '✕' : '☰'}</span>
        </button>
        <div id="site-menu" className={`nav-menu${menuOpen ? ' open' : ''}`}>
          <nav className="nav-links" aria-label="Main">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={cls}>
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="nav-auth">
            {user ? (
              <>
                <span className="nav-greeting">Hi, {user.first_name}</span>
                <button
                  className="btn btn-light"
                  onClick={async () => {
                    await logout()
                    navigate('/')
                  }}
                >
                  Log Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={cls}>
                  Log In
                </NavLink>
                <NavLink to="/signup" className="btn btn-light">
                  Create Account
                </NavLink>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
