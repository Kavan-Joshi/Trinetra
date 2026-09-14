import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getRole } from '../api'

const PROTOCOL_STYLES: Record<string, string> = {
  rtsp: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  onvif: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/40',
  'http-mjpeg': 'bg-teal-500/15 text-teal-300 border-teal-500/40',
  'vendor-api': 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  gb28181: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
}

export default function CamerasPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState<any[]>([])
  const [depts, setDepts] = useState<any[]>([])
  const [zone, setZone] = useState('')
  const [status, setStatus] = useState('')
  const [deptId, setDeptId] = useState('')
  const [health, setHealth] = useState('')
  const [maintenance, setMaintenance] = useState('')
  const isAdmin = getRole() === 'admin'

  useEffect(() => {
    api('/api/v1/departments').then((r) => setDepts(r.items)).catch(() => {})
  }, [])

  useEffect(() => {
    const q = new URLSearchParams()
    if (zone) q.set('zone', zone)
    if (status) q.set('status', status)
    if (deptId) q.set('department_id', deptId)
    if (health) q.set('health', health)
    if (maintenance) q.set('maintenance_status', maintenance)
    api(`/api/v1/cameras?${q}`).then((r) => setItems(r.items)).catch(() => {})
  }, [zone, status, deptId, health, maintenance])

  const exportCsv = () => {
    const q = new URLSearchParams()
    if (zone) q.set('zone', zone)
    if (deptId) q.set('department_id', deptId)
    if (health) q.set('health', health)
    const token = localStorage.getItem('trinetra_token') ?? ''
    fetch(`/api/v1/cameras/export?${q}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((b) => {
        const url = URL.createObjectURL(b)
        const a = document.createElement('a')
        a.href = url; a.download = 'trinetra-camera-registry.csv'; a.click()
        URL.revokeObjectURL(url)
      })
  }

  const zones = Array.from(new Set(items.map((c) => c.zone)))
  const online = items.filter((c) => c.status === 'online').length

  const toggle = async (cam: any) => {
    await api(`/api/v1/cameras/${cam.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: cam.status === 'online' ? 'offline' : 'online' }),
    })
    setItems((prev) => prev.map((c) => (c.id === cam.id ? { ...c, status: c.status === 'online' ? 'offline' : 'online' } : c)))
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-xl font-semibold">
          Camera Registry <span className="text-sm text-slate-500 font-normal">({items.length} registered · {online} online)</span>
        </h1>
        <div className="flex gap-2 flex-wrap">
          <select value={deptId} onChange={(e) => setDeptId(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All departments</option>
            {depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={zone} onChange={(e) => setZone(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All zones</option>
            {zones.map((z) => <option key={z} value={z}>{z}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All statuses</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
          </select>
          <select value={health} onChange={(e) => setHealth(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All health</option>
            <option value="healthy">Healthy</option>
            <option value="degraded">Degraded</option>
            <option value="offline">Offline</option>
          </select>
          <select value={maintenance} onChange={(e) => setMaintenance(e.target.value)} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm">
            <option value="">All maintenance</option>
            <option value="ok">OK</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_repair">In repair</option>
          </select>
          <button onClick={exportCsv} className="border border-slate-700 hover:border-slate-500 rounded px-3 py-1.5 text-sm">Export CSV</button>
        </div>
      </div>
      <div className="overflow-auto border border-slate-800 rounded-lg max-h-[70vh]">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase sticky top-0">
            <tr>
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Location</th>
              <th className="p-2 text-left">Vendor</th>
              <th className="p-2 text-left">VMS Platform</th>
              <th className="p-2 text-left">Protocol</th>
              <th className="p-2 text-left">Department</th>
              <th className="p-2 text-left">Zone</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Health</th>
              <th className="p-2 text-left">Live</th>
              {isAdmin && <th className="p-2 text-left">Action</th>}
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2 text-slate-500">{c.id}</td>
                <td className="p-2">
                  {c.name}
                  {c.source_type === 'community' && (
                    <span className="ml-2 text-[10px] px-1 py-0.5 rounded border bg-emerald-500/15 text-emerald-300 border-emerald-500/40">community</span>
                  )}
                </td>
                <td className="p-2 text-slate-400">{c.vendor}</td>
                <td className="p-2 text-slate-400">{c.vms}</td>
                <td className="p-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${PROTOCOL_STYLES[c.protocol] || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                    {c.protocol}
                  </span>
                </td>
                <td className="p-2 text-slate-400">{c.department}</td>
                <td className="p-2 text-slate-400">{c.zone}</td>
                <td className="p-2">
                  <span className="flex items-center gap-1.5 text-xs">
                    <span className={`w-2 h-2 rounded-full ${c.status === 'online' ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                    {c.status}
                  </span>
                </td>
                <td className="p-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    c.health === 'healthy' ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                    : c.health === 'degraded' ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                    : 'bg-slate-800 text-slate-500 border-slate-700'
                  }`}>{c.health}{c.maintenance_status && c.maintenance_status !== 'ok' ? ` · ${c.maintenance_status}` : ''}</span>
                </td>
                <td className="p-2">
                  <button onClick={() => navigate(`/live?cam=${c.id}`)} className="text-xs text-brand-400 hover:text-brand-300 border border-brand-500/40 rounded px-2 py-1">
                    Watch
                  </button>
                </td>
                {isAdmin && (
                  <td className="p-2">
                    <button onClick={() => toggle(c)} className="text-xs border border-slate-700 hover:border-slate-500 rounded px-2 py-1 text-slate-300">
                      {c.status === 'online' ? 'Set offline' : 'Set online'}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
