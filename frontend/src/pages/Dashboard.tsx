import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AlertCard from '../components/AlertCard'
import { api } from '../api'
import { connectAlerts } from '../ws'

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<any>(null)
  const [alerts, setAlerts] = useState<any[]>([])

  useEffect(() => {
    const load = () => api('/api/v1/stats/overview').then(setStats).catch(() => {})
    load()
    const t = setInterval(load, 10000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    api('/api/v1/alerts?limit=25')
      .then((r) => setAlerts(r.items))
      .catch(() => {})
    return connectAlerts((a) => setAlerts((prev) => [a, ...prev].slice(0, 50)))
  }, [])

  const cards = [
    { label: 'Cameras online', value: stats ? `${stats.cameras_online}/${stats.cameras_total}` : '—' },
    { label: 'Events (24h)', value: stats?.events_24h ?? '—' },
    { label: 'Active alerts', value: stats?.alerts_active ?? '—' },
    { label: 'Watchlist entries', value: stats?.watchlist_active ?? '—' },
  ]

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-xl font-semibold">Command Dashboard</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c) => (
          <div key={c.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-2xl font-bold text-brand-400">{c.value}</div>
            <div className="text-xs text-slate-500 mt-1">{c.label}</div>
          </div>
        ))}
      </div>
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium">Live alert feed</h2>
          <span className="text-xs text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse inline-block" />
            streaming
          </span>
        </div>
        <div className="space-y-2 max-h-[62vh] overflow-auto pr-1">
          {alerts.length === 0 && (
            <div className="text-sm text-slate-600 text-center py-10 border border-dashed border-slate-800 rounded-lg">
              No alerts yet — detections stream in real time from the federated gateways.
            </div>
          )}
          {alerts.map((a) => (
            <AlertCard key={a.alert_id} alert={a} onTrack={(plate) => navigate(`/map?plate=${encodeURIComponent(plate)}`)} />
          ))}
        </div>
      </div>
    </div>
  )
}
