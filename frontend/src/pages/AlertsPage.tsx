import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, fmtTime } from '../api'
import { connectAlerts } from '../ws'

const STATUSES = ['', 'new', 'ack', 'resolved']
const CATEGORIES = ['', 'stolen_vehicle', 'blacklisted_vehicle', 'wanted_person', 'missing_person', 'suspect', 'anomaly']

export default function AlertsPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  const load = useCallback(() => {
    const q = new URLSearchParams({ limit: '200' })
    if (status) q.set('status', status)
    if (category) q.set('category', category)
    api(`/api/v1/alerts?${q}`).then((r) => {
      setItems(r.items)
      setTotal(r.total)
    }).catch(() => {})
  }, [status, category])

  useEffect(() => {
    load()
    return connectAlerts(() => load())
  }, [load])

  const patch = async (alertId: string, newStatus: string) => {
    await api(`/api/v1/alerts/${alertId}`, { method: 'PATCH', body: JSON.stringify({ status: newStatus }) })
    load()
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-semibold">Alerts <span className="text-sm text-slate-500 font-normal">({total})</span></h1>
        <div className="flex gap-2">
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            {STATUSES.map((s) => <option key={s} value={s}>{s === '' ? 'All statuses' : s}</option>)}
          </select>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            {CATEGORIES.map((c) => <option key={c} value={c}>{c === '' ? 'All categories' : c.replace('_', ' ')}</option>)}
          </select>
        </div>
      </div>
      <div className="overflow-auto border border-slate-800 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase">
            <tr>
              <th className="p-2 text-left">Evidence</th>
              <th className="p-2 text-left">Alert</th>
              <th className="p-2 text-left">Camera</th>
              <th className="p-2 text-left">Time</th>
              <th className="p-2 text-left">Confidence</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.alert_id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2">
                  {a.snapshot_path ? (
                    <img src={`/evidence/${a.snapshot_path}`} className="w-24 h-14 object-cover rounded border border-slate-800" alt="evidence" />
                  ) : (
                    <span className="text-slate-700 text-xs">—</span>
                  )}
                </td>
                <td className="p-2 max-w-xs">
                  <div className="truncate">{a.title}</div>
                  {a.description && <div className="text-xs text-slate-500 truncate">{a.description}</div>}
                </td>
                <td className="p-2 text-slate-400">{a.camera_id}</td>
                <td className="p-2 text-slate-400 whitespace-nowrap">{fmtTime(a.ts)}</td>
                <td className="p-2 text-slate-400">{(a.confidence * 100).toFixed(0)}%</td>
                <td className="p-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${
                    a.status === 'new' ? 'bg-red-500/15 text-red-300 border-red-500/40'
                    : a.status === 'ack' ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                    : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                  }`}>{a.status}</span>
                </td>
                <td className="p-2">
                  <div className="flex gap-1.5">
                    {a.plate && (
                      <button onClick={() => navigate(`/map?plate=${encodeURIComponent(a.plate)}`)} className="text-xs text-brand-400 border border-brand-500/40 rounded px-2 py-1 hover:text-brand-300">
                        Track
                      </button>
                    )}
                    {a.status === 'new' && (
                      <button onClick={() => patch(a.alert_id, 'ack')} className="text-xs text-amber-300 border border-amber-500/40 rounded px-2 py-1 hover:text-amber-200">
                        Ack
                      </button>
                    )}
                    {a.status !== 'resolved' && (
                      <button onClick={() => patch(a.alert_id, 'resolved')} className="text-xs text-emerald-300 border border-emerald-500/40 rounded px-2 py-1 hover:text-emerald-200">
                        Resolve
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-slate-600 text-sm">No alerts match the filter.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
