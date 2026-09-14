import { useEffect, useState } from 'react'
import { api, getRole } from '../api'

export default function DepartmentsPage() {
  const [items, setItems] = useState<any[]>([])
  const [report, setReport] = useState<any | null>(null)
  const [msg, setMsg] = useState('')
  const isAdmin = getRole() === 'admin'

  const load = () => {
    api('/api/v1/departments').then((r) => setItems(r.items)).catch(() => {})
    if (isAdmin) api('/api/v1/departments/retention/report').then(setReport).catch(() => {})
  }

  useEffect(load, [])

  const saveRetention = async (id: number, field: 'retention_events_days' | 'retention_evidence_days', value: number) => {
    setMsg('')
    try {
      await api(`/api/v1/departments/${id}`, { method: 'PATCH', body: JSON.stringify({ [field]: value }) })
      setMsg('Retention policy updated.')
      load()
    } catch (e: any) {
      setMsg(e.message)
    }
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Departments <span className="text-sm text-slate-500 font-normal">({items.length} onboarded)</span></h1>
      {msg && <div className="text-xs text-brand-300">{msg}</div>}
      <div className="overflow-auto border border-slate-800 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase">
            <tr>
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Department</th>
              <th className="p-2 text-left">Cameras</th>
              <th className="p-2 text-left">Event retention (days)</th>
              <th className="p-2 text-left">Evidence retention (days)</th>
            </tr>
          </thead>
          <tbody>
            {items.map((d) => (
              <tr key={d.id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2 text-slate-500 font-mono text-xs">{d.code}</td>
                <td className="p-2">{d.name}</td>
                <td className="p-2 text-slate-400">{d.camera_count ?? '—'}</td>
                <td className="p-2">
                  {isAdmin ? (
                    <input
                      type="number"
                      defaultValue={d.retention_events_days}
                      onBlur={(e) => saveRetention(d.id, 'retention_events_days', parseInt(e.target.value, 10) || 0)}
                      className="w-20 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-sm"
                    />
                  ) : d.retention_events_days}
                </td>
                <td className="p-2">
                  {isAdmin ? (
                    <input
                      type="number"
                      defaultValue={d.retention_evidence_days}
                      onBlur={(e) => saveRetention(d.id, 'retention_evidence_days', parseInt(e.target.value, 10) || 0)}
                      className="w-20 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-sm"
                    />
                  ) : d.retention_evidence_days}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isAdmin && report && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="font-medium text-sm mb-2">
            Retention dry-run report
            <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded border ${report.dry_run ? 'bg-amber-500/15 text-amber-300 border-amber-500/40' : 'bg-red-500/15 text-red-300 border-red-500/40'}`}>
              {report.dry_run ? 'DRY-RUN (no deletion)' : 'PURGE ENABLED'}
            </span>
          </div>
          <div className="text-xs text-slate-400 mb-2">{report.total_events_to_purge} event(s) eligible for purge across all departments.</div>
          <div className="overflow-auto max-h-48">
            <table className="w-full text-xs">
              <thead className="text-slate-500 uppercase">
                <tr>
                  <th className="p-1.5 text-left">Department</th>
                  <th className="p-1.5 text-left">Events to purge</th>
                  <th className="p-1.5 text-left">Cutoff</th>
                </tr>
              </thead>
              <tbody>
                {report.items.filter((r: any) => r.events_to_purge > 0).map((r: any) => (
                  <tr key={r.department_id} className="border-t border-slate-800/70">
                    <td className="p-1.5">{r.name}</td>
                    <td className="p-1.5 text-amber-300">{r.events_to_purge}</td>
                    <td className="p-1.5 text-slate-500">{new Date(r.cutoff).toLocaleString('en-IN', { hour12: false })}</td>
                  </tr>
                ))}
                {report.items.filter((r: any) => r.events_to_purge > 0).length === 0 && (
                  <tr><td colSpan={3} className="p-3 text-center text-slate-600">No events currently past retention.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
