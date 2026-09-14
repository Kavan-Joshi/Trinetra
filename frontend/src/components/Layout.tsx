import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearAuth, getDepartmentId, getDisplayName, getRole } from '../api'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '▦' },
  { to: '/map', label: 'Live Map', icon: '◎' },
  { to: '/live', label: 'Live View', icon: '▶' },
  { to: '/grid', label: 'Camera Grid', icon: '▣' },
  { to: '/alerts', label: 'Alerts', icon: '⚠' },
  { to: '/notifications', label: 'Fan-out', icon: '✈' },
  { to: '/events', label: 'Event Search', icon: '⌕' },
  { to: '/watchlist', label: 'Watchlist', icon: '☰' },
  { to: '/cameras', label: 'Cameras', icon: '⌾' },
  { to: '/gap-analysis', label: 'Gap Analysis', icon: '⬓' },
  { to: '/departments', label: 'Departments', icon: '⬡' },
  { to: '/records', label: 'Records', icon: '⚖' },
  { to: '/community', label: 'Community', icon: '⌂' },
]

export default function Layout() {
  const navigate = useNavigate()
  const role = getRole()
  const dept = getDepartmentId()

  return (
    <div className="flex h-full">
      <aside className="w-52 shrink-0 border-r border-slate-800 bg-slate-900/70 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-800">
          <div className="text-xl font-bold tracking-widest text-brand-400">TRINETRA</div>
          <div className="text-[10px] text-slate-500 mt-1 leading-tight">
            Integrated Video Management<br />&amp; Analytics Platform
          </div>
        </div>
        <nav className="flex-1 py-3 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2 text-sm mx-2 rounded ${
                  isActive ? 'bg-brand-500/15 text-brand-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <span className="w-4 text-center">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-800 text-xs">
          <div className="text-slate-300 font-medium">{getDisplayName() || 'User'}</div>
          <div className="text-slate-500 uppercase tracking-wide text-[10px]">{role}{dept ? ` · dept #${dept}` : ' · global'}</div>
          <button
            onClick={() => {
              clearAuth()
              navigate('/login')
            }}
            className="mt-3 text-slate-400 hover:text-red-300 border border-slate-700 rounded px-2 py-1 w-full"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
