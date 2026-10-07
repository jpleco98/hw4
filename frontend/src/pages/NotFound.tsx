import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="section">
      <h1>Page not found</h1>
      <p>
        That page wandered off campus. <Link to="/">Head back home</Link>.
      </p>
    </section>
  )
}
