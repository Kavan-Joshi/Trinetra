import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Circle, CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet'
import { api, fmtTime, normPlate } from '../api'
import { connectAlerts } from '../ws'

const HEALTH_COLOR: Record<string, string> = {
  healthy: '#10b981', degraded: '#f59e0b', offline: '#64748b',
}

export default function MapView() {
  const [params, setParams] = useSearchParams()
  const [cameras, setCameras] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [recent, setRecent] = useState<any[]>([])
  const [route, setRoute] = useState<any>(null)
  const [input, setInput] = useState(params.get('plate') ?? '')
  const [target, setTarget] = useState(params.get('plate') ?? '')
  const [liveFollow, setLiveFollow] = useState(true)
  const [showCoverage, setShowCoverage] = useState(false)
  const [tick, setTick] = useState(0)
  const followRef = useRef(true)
  followRef.current = liveFollow

  useEffect(() => {
    api('/api/v1/cameras?limit=500')
      .then((r) => setCameras(r.items))
      .catch(() => {})
    api('/api/v1/alerts?limit=150')
      .then((r) => setAlerts(r.items))
      .catch(() => {})
  }, [])

  useEffect(() => {
    return connectAlerts((a) => {
      setAlerts((prev) => [a, ...prev].slice(0, 200))
      if (followRef.current && a.plate && normPlate(a.plate) === normPlate(target)) {
        setTick((t) => t + 1)
      }
    })
  }, [target])

  useEffect(() => {
    if (!target) return
    api(`/api/v1/tracking/${encodeURIComponent(target)}/route`)
      .then(setRoute)
      .catch(() => setRoute(null))
    setParams({ plate: target })
  }, [target, tick])

  useEffect(() => {
    const load = () => api('/api/v1/tracking/recent').then((r) => setRecent(r.items)).catch(() => {})
    load()
    const t = setInterval(load, 8000)
    return () => clearInterval(t)
  }, [tick])

  const session = route?.sessions?.[0] ?? null
  const trail = useMemo(
    () => (session ? session.points.map((p: any) => [p.lat, p.lon] as [number, number]) : []),
    [session],
  )

  const track = (plate: string) => {
    const clean = plate.trim()
    if (!clean) return
    setTarget(clean)
    setInput(clean)
    setTick((t) => t + 1)
  }

  return (
    <div className="flex h-full">
      <div className="w-80 shrink-0 border-r border-slate-800 bg-slate-900/40 p-4 space-y-4 overflow-auto">
        <div>
          <div className="text-xs text-slate-500 mb-1">Track vehicle by plate</div>
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && track(input)}
              placeholder="GJ-01-KA-1234"
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm outline-none focus:border-brand-500"
            />
            <button onClick={() => track(input)} className="bg-brand-600 hover:bg-brand-500 rounded px-3 text-sm">
              Track
            </button>
          </div>
          <label className="flex items-center gap-2 mt-2 text-xs text-slate-400 cursor-pointer">
            <input type="checkbox" checked={liveFollow} onChange={(e) => setLiveFollow(e.target.checked)} />
            Live-follow on new alerts
          </label>
          <label className="flex items-center gap-2 mt-1 text-xs text-slate-400 cursor-pointer">
            <input type="checkbox" checked={showCoverage} onChange={(e) => setShowCoverage(e.target.checked)} />
            Show coverage footprints
          </label>
        </div>

        {session && (
          <div className="bg-slate-900 border border-brand-500/40 rounded-lg p-3 space-y-1">
            <div className="text-brand-400 font-semibold">{route.display_plate}</div>
            <div className="text-xs text-slate-400">{session.points.length} camera passes</div>
            <div className="text-xs text-slate-500">
              First seen {fmtTime(session.points[0].ts)}
              <br />
              Last seen {fmtTime(session.points[session.points.length - 1].ts)}
            </div>
          </div>
        )}

        <div>
          <div className="text-xs text-slate-500 mb-2">Recently tracked</div>
          <div className="space-y-1.5">
            {recent.slice(0, 12).map((r: any) => (
              <button
                key={r.plate_norm}
                onClick={() => track(r.plate)}
                className={`w-full text-left text-xs px-2 py-1.5 rounded border ${
                  normPlate(target) === r.plate_norm
                    ? 'border-brand-500/60 bg-brand-500/10 text-brand-300'
                    : 'border-slate-800 hover:border-slate-600 text-slate-300'
                }`}
              >
                <span className="font-medium">{r.plate}</span>
                <span className="text-slate-500"> · {r.last_camera} · {fmtTime(r.last_seen)}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="text-[10px] text-slate-600 leading-relaxed pt-2 border-t border-slate-800">
          Green: healthy · Amber: degraded · Gray: offline · Red: alert pin · Blue trail: tracked route.
        </div>
      </div>

      <div className="flex-1">
        <MapContainer center={[23.12, 72.58]} zoom={11} className="h-full w-full" scrollWheelZoom>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {cameras.map((c) => (
            <CircleMarker
              key={c.id}
              center={[c.lat, c.lon]}
              radius={4}
              pathOptions={{
                color: c.status === 'online' ? HEALTH_COLOR[c.health] || '#10b981' : '#475569',
                fillColor: c.status === 'online' ? HEALTH_COLOR[c.health] || '#10b981' : '#475569',
                fillOpacity: 0.9,
                weight: 1,
              }}
            >
              <Tooltip>{`${c.id} — ${c.name} · ${c.vendor} · ${c.protocol} · ${c.health}`}</Tooltip>
            </CircleMarker>
          ))}
          {showCoverage && cameras.map((c) => (
            <Circle
              key={`cov-${c.id}`}
              center={[c.lat, c.lon]}
              radius={c.coverage_radius_m || 80}
              pathOptions={{
                color: HEALTH_COLOR[c.health] || '#10b981',
                fillColor: HEALTH_COLOR[c.health] || '#10b981',
                fillOpacity: 0.08,
                weight: 1,
              }}
            />
          ))}
          {alerts.map((a) => (
            <CircleMarker
              key={a.alert_id}
              center={[a.lat, a.lon]}
              radius={7}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.55, weight: 2 }}
            >
              <Tooltip>{`${a.title} — ${fmtTime(a.ts)}`}</Tooltip>
            </CircleMarker>
          ))}
          {trail.length > 1 && (
            <Polyline positions={trail} pathOptions={{ color: '#38bdf8', weight: 4, opacity: 0.85 }} />
          )}
          {session?.points.map((p: any, i: number) => (
            <CircleMarker
              key={`${p.camera_id}-${i}`}
              center={[p.lat, p.lon]}
              radius={6}
              pathOptions={{ color: '#38bdf8', fillColor: '#0f172a', fillOpacity: 1, weight: 2 }}
            >
              <Tooltip>{`#${i + 1} ${p.camera_id} — ${p.camera_name} · ${fmtTime(p.ts)}`}</Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
