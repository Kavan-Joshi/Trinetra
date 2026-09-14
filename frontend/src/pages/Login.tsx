import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setAuth } from '../api'

const QUICK = [
  { u: 'admin', p: 'admin123', label: 'Admin' },
  { u: 'operator', p: 'operator123', label: 'Operator' },
  { u: 'analyst', p: 'analyst123', label: 'Analyst' },
  { u: 'traffic', p: 'traffic123', label: 'Traffic' },
  { u: 'rto', p: 'rto123', label: 'RTO' },
]

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      })
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Login failed')
      const data = await res.json()
      setAuth(data.access_token, data.role, data.display_name, data.department_id)
      navigate('/')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center p-6">
      <div className="w-full max-w-4xl grid md:grid-cols-2 gap-8 items-center">
        <div>
          <div className="text-4xl font-bold tracking-widest text-brand-400">TRINETRA</div>
          <p className="mt-4 text-slate-400 leading-relaxed">
            Federated video management &amp; AI analytics for Gujarat Police. 50 heterogeneous
            cameras, one event stream. Edge detection, central correlation, live watchlist alerts,
            and cross-camera vehicle tracking on GIS.
          </p>
          <div className="mt-6 text-xs text-slate-600">
            Gujarat Police Innovation Challenge 2026 — field validation build
          </div>
        </div>
        <form onSubmit={submit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="text-lg font-semibold">Sign in</div>
          <input
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm outline-none focus:border-brand-500"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm outline-none focus:border-brand-500"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <div className="text-red-400 text-xs">{error}</div>}
          <button
            disabled={busy}
            className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded py-2 text-sm font-medium"
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
          <div className="flex gap-2 justify-center pt-2">
            {QUICK.map((q) => (
              <button
                key={q.label}
                type="button"
                onClick={() => {
                  setUsername(q.u)
                  setPassword(q.p)
                }}
                className="text-xs text-slate-400 hover:text-brand-400 border border-slate-800 rounded px-3 py-1"
              >
                {q.label}
              </button>
            ))}
          </div>
        </form>
      </div>
    </div>
  )
}
