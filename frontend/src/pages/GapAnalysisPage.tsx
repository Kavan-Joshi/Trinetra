import { useEffect, useState } from 'react'
import { api } from '../api'

export default function GapAnalysisPage() {
  const [report, setReport] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    api('/api/v1/gap-analysis/report').then(setReport).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const download = () => {
    const token = localStorage.getItem('trinetra_token') ?? ''
    fetch('/api/v1/gap-analysis/report/download', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((b) => {
        const url = URL.createObjectURL(b)
        const a = document.createElement('a')
        a.href = url
        a.download = 'trinetra-gap-analysis-report.csv'
        a.click()
        URL.revokeObjectURL(url)
      })
  }

  const s = report?.summary
  const cov = report?.coverage
  const age = report?.ageing

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold">Gap Analysis & Infrastructure Assessment</h1>
          <p className="text-xs text-slate-500 mt-1">
            Coverage gaps by zone + ageing infrastructure — the Model-1 planning layer for future integration,
            gap identification, and infrastructure decision support.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} disabled={loading} className="border border-slate-700 hover:border-slate-500 rounded px-3 py-1.5 text-sm">
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
          <button onClick={download} className="bg-brand-600 hover:bg-brand-500 rounded px-3 py-1.5 text-sm">Download report (CSV)</button>
        </div>
      </div>

      {report && s && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <Card label="Zones assessed" value={s.zones_assessed} />
            <Card label="Zones w/ coverage gaps" value={s.zones_with_coverage_gaps} warn={s.zones_with_coverage_gaps > 0} />
            <Card label="Ageing cameras (5y+)" value={s.ageing_cameras} warn={s.ageing_cameras > 0} />
            <Card label="EOL firmware (v2.x)" value={s.end_of_life_firmware} warn={s.end_of_life_firmware > 0} />
            <Card label="Need maintenance" value={s.cameras_needing_maintenance} warn={s.cameras_needing_maintenance > 0} />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="font-medium text-sm mb-3">Coverage by zone</div>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-slate-500 text-xs uppercase">
                  <tr>
                    <th className="p-2 text-left">Zone</th>
                    <th className="p-2 text-left">Cameras</th>
                    <th className="p-2 text-left">Online</th>
                    <th className="p-2 text-left">Degraded</th>
                    <th className="p-2 text-left">Offline</th>
                    <th className="p-2 text-left">In repair</th>
                    <th className="p-2 text-left">Coverage km²</th>
                    <th className="p-2 text-left">Online ratio</th>
                    <th className="p-2 text-left">Gap</th>
                  </tr>
                </thead>
                <tbody>
                  {cov.items.map((z: any) => (
                    <tr key={z.zone} className={`border-t border-slate-800/70 ${z.gap ? 'bg-red-500/5' : ''}`}>
                      <td className="p-2">{z.zone}</td>
                      <td className="p-2 text-slate-400">{z.total}</td>
                      <td className="p-2 text-emerald-300">{z.online}</td>
                      <td className="p-2 text-amber-300">{z.degraded}</td>
                      <td className="p-2 text-slate-500">{z.offline}</td>
                      <td className="p-2 text-amber-300">{z.in_repair}</td>
                      <td className="p-2 text-slate-400">{z.coverage_km2}</td>
                      <td className="p-2 text-slate-400">{(z.online_ratio * 100).toFixed(0)}%</td>
                      <td className="p-2">
                        {z.gap ? <span className="text-red-300 text-xs px-1.5 py-0.5 rounded border border-red-500/40 bg-red-500/10">GAP</span>
                          : <span className="text-emerald-300 text-xs">ok</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="font-medium text-sm mb-3">Ageing infrastructure</div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <AgeRow label="Under 2 years" count={age.counts.under_2y} />
                <AgeRow label="2–5 years" count={age.counts['2_to_5y']} />
                <AgeRow label="5–7 years (ageing)" count={age.counts['5_to_7y']} warn />
                <AgeRow label="Over 7 years (critical)" count={age.counts.over_7y} warn />
              </div>
              <div className="mt-3 text-xs text-slate-500">
                End-of-life firmware: <span className="text-amber-300">{age.eol_firmware_count}</span> ·
                Needing maintenance: <span className="text-amber-300">{age.maintenance_issue_count}</span>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <div className="font-medium text-sm mb-3">Recommendations</div>
              <ul className="space-y-2 text-sm text-slate-300 list-disc list-inside">
                {report.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          </div>
        </>
      )}
      {!report && !loading && <div className="text-slate-600 text-sm">No report data.</div>}
    </div>
  )
}

function Card({ label, value, warn }: { label: string; value: any; warn?: boolean }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className={`text-2xl font-bold ${warn ? 'text-amber-400' : 'text-brand-400'}`}>{value ?? '—'}</div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
    </div>
  )
}

function AgeRow({ label, count, warn }: { label: string; count: number; warn?: boolean }) {
  return (
    <div className="flex items-center justify-between border border-slate-800 rounded px-3 py-2">
      <span className="text-slate-400">{label}</span>
      <span className={`font-medium ${warn ? 'text-amber-300' : 'text-slate-200'}`}>{count}</span>
    </div>
  )
}
