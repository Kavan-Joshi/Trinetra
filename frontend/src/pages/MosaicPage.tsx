import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Hls from 'hls.js'
import { api } from '../api'

export default function MosaicPage() {
  const navigate = useNavigate()
  const [cameras, setCameras] = useState<any[]>([])
  const [cols, setCols] = useState(3)

  useEffect(() => {
    api('/api/v1/cameras?limit=500').then((r) => {
      // grid cameras first (cam01..cam30), then any others
      const grid = r.items.filter((c: any) => /^cam\d+$/i.test(c.id))
      const rest = r.items.filter((c: any) => !/^cam\d+$/i.test(c.id))
      setCameras([...grid, ...rest])
    }).catch(() => {})
  }, [])

  const gridStyle = useMemo(() => ({ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }), [cols])

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold">Live Camera Grid <span className="text-sm text-slate-500 font-normal">({cameras.length} cameras)</span></h1>
          <p className="text-xs text-slate-500 mt-1">All cameras streaming in real time. Tiles lazy-load as you scroll. Click any tile for full view.</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-500 text-xs">Columns</span>
          {[3, 4, 5, 6].map((n) => (
            <button key={n} onClick={() => setCols(n)} className={`w-8 h-8 rounded border ${cols === n ? 'bg-brand-600 text-white border-brand-500' : 'border-slate-700 text-slate-400 hover:border-slate-500'}`}>{n}</button>
          ))}
        </div>
      </div>
      <div className="grid gap-2" style={gridStyle}>
        {cameras.map((c) => (
          <CameraTile key={c.id} cam={c} onOpen={(id) => navigate(`/live?cam=${id}`)} />
        ))}
      </div>
    </div>
  )
}

function CameraTile({ cam, onOpen }: { cam: any; onOpen: (id: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const [state, setState] = useState<'idle' | 'live' | 'error'>('idle')

  useEffect(() => {
    const wrap = wrapRef.current
    const video = videoRef.current
    if (!wrap || !video) return

    const start = () => {
      if (hlsRef.current) return
      const url = `/stream/hls/${cam.id}/playlist.m3u8`
      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url
        video.play().catch(() => {})
      } else if (Hls.isSupported()) {
        const hls = new Hls({ lowLatencyMode: true, maxBufferLength: 6, liveSyncDuration: 2 })
        hlsRef.current = hls
        hls.loadSource(url)
        hls.attachMedia(video)
        hls.on(Hls.Events.MANIFEST_PARSED, () => { setState('live'); video.play().catch(() => {}) })
        hls.on(Hls.Events.ERROR, (_e, data) => {
          if (!data.fatal) return
          if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            // likely the streamer's concurrent-stream cap (503) — retry until a slot frees
            setState('idle')
            setTimeout(() => { if (hlsRef.current) hls.startLoad() }, 4000)
          } else {
            setState('error'); hls.destroy(); hlsRef.current = null
          }
        })
      }
    }
    const stop = () => {
      if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null }
      video.removeAttribute('src')
      video.load()
      setState('idle')
    }

    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => e.isIntersecting ? start() : stop())
    }, { rootMargin: '100px' })
    io.observe(wrap)
    return () => { io.disconnect(); stop() }
  }, [cam.id])

  return (
    <div ref={wrapRef} onClick={() => onOpen(cam.id)}
      className="relative bg-black rounded-lg border border-slate-800 overflow-hidden cursor-pointer hover:border-brand-500/60 aspect-video">
      <video ref={videoRef} muted autoPlay playsInline className="w-full h-full object-cover" />
      <div className="absolute top-1.5 left-1.5 text-[10px] font-mono bg-black/60 px-1.5 py-0.5 rounded text-slate-200">{cam.id}</div>
      <div className={`absolute top-1.5 right-1.5 text-[9px] px-1.5 py-0.5 rounded flex items-center gap-1 ${
        state === 'live' ? 'bg-red-500/80 text-white' : state === 'error' ? 'bg-slate-700 text-slate-300' : 'bg-slate-800/80 text-slate-400'
      }`}>
        {state === 'live' && <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
        {state === 'live' ? 'LIVE' : state === 'error' ? 'ERR' : '…'}
      </div>
      {state !== 'live' && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-xs">
          {state === 'error' ? 'stream unavailable' : 'connecting…'}
        </div>
      )}
    </div>
  )
}
