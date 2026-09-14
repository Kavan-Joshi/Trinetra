import { useEffect, useState } from 'react'
import { api, fmtTime } from '../api'

export default function EventsPage() {
  const [cameras, setCameras] = useState<any[]>([])
  const [plate, setPlate] = useState('')
  const [cameraId, setCameraId] = useState('')
  const [kind, setKind] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    api('/api/v1/cameras?limit=500').then((r) => setCameras(r.items)).catch(() => {})
  }, [])

  const search = () => {
    const q = new URLSearchParams({ limit: '200' })
    if (plate) q.set('plate', plate)
    if (cameraId) q.set('camera_id', cameraId)
    if (kind) q.set('kind', kind)
    if (from) q.set('date_from', new Date(from).toISOString())
    if (to) q.set('date_to', new Date(to).toISOString())
    api(`/api/v1/events?${q}`).then((r) => {
      setItems(r.items)
      setTotal(r.total)
    }).catch(() => {})
  }

  useEffect(search, [])

  const exportCsv = () => {
    const header = 'timestamp,camera_id,kind,plate,vehicle_class,color,direction,speed_kmh,confidence'
    const rows = items.map((e) => [
      e.ts, e.camera_id, e.kind, e.plate ?? '', e.vehicle_class ?? '', e.color ?? '',
      e.direction ?? '', e.speed_kmh ?? '', e.plate_confidence ?? '',
    ].join(','))
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'trinetra-events.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Event Search <span className="text-sm text-slate-500 font-normal">({total} matches)</span></h1>
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
        <div>
          <label className="text-xs text-slate-500">Plate</label>
          <input value={plate} onChange={(e) => setPlate(e.target.value)} placeholder="GJ-01…" className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="text-xs text-slate-500">Camera</label>
          <select value={cameraId} onChange={(e) => setCameraId(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All</option>
            {cameras.map((c) => <option key={c.id} value={c.id}>{c.id}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500">Type</label>
          <select value={kind} onChange={(e) => setKind(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All</option>
            <option value="vehicle">Vehicle</option>
            <option value="person">Person</option>
            <option value="object">Object</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500">From</label>
          <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
        </div>
        <div>
          <label className="text-xs text-slate-500">To</label>
          <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
        </div>
        <div className="flex gap-2">
          <button onClick={search} className="bg-brand-600 hover:bg-brand-500 rounded px-4 py-1.5 text-sm flex-1">Search</button>
          <button onClick={exportCsv} className="border border-slate-700 hover:border-slate-500 rounded px-3 py-1.5 text-sm">CSV</button>
        </div>
      </div>
      <div className="overflow-auto border border-slate-800 rounded-lg max-h-[65vh]">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase sticky top-0">
            <tr>
              <th className="p-2 text-left">Time</th>
              <th className="p-2 text-left">Camera</th>
              <th className="p-2 text-left">Type</th>
              <th className="p-2 text-left">Plate</th>
              <th className="p-2 text-left">Class / Color</th>
              <th className="p-2 text-left">Speed</th>
              <th className="p-2 text-left">Conf.</th>
              <th className="p-2 text-left">Frame</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.event_id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2 whitespace-nowrap text-slate-400">{fmtTime(e.ts)}</td>
                <td className="p-2">{e.camera_id}</td>
                <td className="p-2 text-slate-400">{e.kind}</td>
                <td className="p-2 font-medium text-brand-300">{e.plate ?? '—'}</td>
                <td className="p-2 text-slate-400">{[e.vehicle_class, e.color].filter(Boolean).join(' · ') || '—'}</td>
                <td className="p-2 text-slate-400">{e.speed_kmh ? `${e.speed_kmh} km/h` : '—'}</td>
                <td className="p-2 text-slate-400">{e.plate_confidence ? `${(e.plate_confidence * 100).toFixed(0)}%` : '—'}</td>
                <td className="p-2">
                  {e.snapshot_path ? (
                    <img src={`/evidence/${e.snapshot_path}`} className="w-20 h-12 object-cover rounded border border-slate-800" alt="frame" />
                  ) : <span className="text-slate-700 text-xs">—</span>}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={8} className="p-8 text-center text-slate-600 text-sm">No events match the query.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
