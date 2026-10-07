import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const EMPTY = { first_name: '', last_name: '', email: '', password: '', confirm_password: '' }

// Mirrors the backend rules in backend/main.py (the server re-checks everything).
function checkPassword(pw: string, confirm: string): string {
  if (pw.length < 8) return 'Password must be at least 8 characters.'
  if (!/[A-Za-z]/.test(pw) || !/\d/.test(pw)) return 'Password must include at least one letter and one number.'
  if (pw !== confirm) return 'Passwords do not match.'
  return ''
}

export default function Signup() {
  const { user, signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const set = (k: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  const mismatch = form.confirm_password.length > 0 && form.password !== form.confirm_password

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const problem = checkPassword(form.password, form.confirm_password)
    if (problem) return setError(problem)
    setError('')
    setBusy(true)
    try {
      await signup(form)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section auth">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Join the Bulldog crew</h1>
        <p className="muted">Create an account so the assistant remembers your chats.</p>
        <div className="row">
          <label>
            First name
            <input value={form.first_name} onChange={set('first_name')} required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={set('last_name')} required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Email
          <input type="email" value={form.email} onChange={set('email')} required autoComplete="email" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={form.password}
            onChange={set('password')}
            required
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
          />
          <small className="hint">At least 8 characters, with a letter and a number.</small>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            value={form.confirm_password}
            onChange={set('confirm_password')}
            required
            maxLength={128}
            autoComplete="new-password"
            aria-invalid={mismatch}
          />
          {mismatch && <small className="hint hint-error">Passwords do not match.</small>}
        </label>
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn-block" type="submit" disabled={busy}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="muted">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
