import { useEffect, useState } from 'react'
import { api, fmtTime } from '../api'
import { connectAlerts } from '../ws'

const CHANNEL_STYLES: Record<string, string> = {
  sms: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  email: 'bg-teal-500/15 text-teal-300 border-teal-500/40',
  webhook: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  fcm: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40',
}

const CHANNELS = ['', 'sms', 'email', 'webhook', 'fcm']

export default function NotificationsPage() {
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [channel, setChannel] = useState('')

  const load = () => {
    const q = new URLSearchParams({ limit: '200' })
    if (channel) q.set('channel', channel)
    api(`/api/v1/notifications?${q}`).then((r) => { setItems(r.items); setTotal(r.total) }).catch(() => {})
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [channel])

  useEffect(() => connectAlerts(() => setTimeout(load, 800)), [])

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold">Alert Fan-out <span className="text-sm text-slate-500 font-normal">({total} dispatches)</span></h1>
          <p className="text-xs text-slate-500 mt-1">Real-time routing of alerts to SMS, email, webhook (CCTNS) and mobile push (FCM).</p>
        </div>
        <select value={channel} onChange={(e) => setChannel(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
          {CHANNELS.map((c) => <option key={c} value={c}>{c === '' ? 'All channels' : c.toUpperCase()}</option>)}
        </select>
      </div>
      <div className="overflow-auto border border-slate-800 rounded-lg max-h-[70vh]">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase sticky top-0">
            <tr>
              <th className="p-2 text-left">Time</th>
              <th className="p-2 text-left">Channel</th>
              <th className="p-2 text-left">Recipient</th>
              <th className="p-2 text-left">Alert</th>
              <th className="p-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((n) => (
              <tr key={n.id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2 whitespace-nowrap text-slate-400">{fmtTime(n.ts)}</td>
                <td className="p-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${CHANNEL_STYLES[n.channel] || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                    {n.channel.toUpperCase()}
                  </span>
                </td>
                <td className="p-2 text-slate-300">{n.recipient}</td>
                <td className="p-2 text-slate-400 max-w-sm truncate">{n.title}</td>
                <td className="p-2">
                  <span className={`text-xs ${n.status === 'sent' ? 'text-emerald-300' : 'text-red-300'}`}>{n.status}</span>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={5} className="p-8 text-center text-slate-600 text-sm">No dispatches yet — alerts are fanned out in real time as they arrive.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
