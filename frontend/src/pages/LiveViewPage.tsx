import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Hls from 'hls.js'
import { api } from '../api'

type Transport = 'hls' | 'webrtc'

export default function LiveViewPage() {
  const [params, setParams] = useSearchParams()
  const [cameras, setCameras] = useState<any[]>([])
  const [selected, setSelected] = useState(params.get('cam') || '')
  const [stream, setStream] = useState<any | null>(null)
  const [transport, setTransport] = useState<Transport>('hls')
  const [status, setStatus] = useState('')
  const [paused, setPaused] = useState(true)
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const reloadTimer = useRef<number | null>(null)

  useEffect(() => {
    api('/api/v1/cameras?limit=500').then((r) => setCameras(r.items)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selected) return
    setStream(null)
    setStatus('Requesting stream…')
    api(`/api/v1/cameras/${selected}/stream`).then((r) => {
      setStream(r)
    }).catch((e) => setStatus(e.message))
  }, [selected])

  const stopAll = () => {
    if (reloadTimer.current) { clearTimeout(reloadTimer.current); reloadTimer.current = null }
    if (hlsRef.current) { hlsRef.current.destroy(); hlsRef.current = null }
    if (pcRef.current) { pcRef.current.close(); pcRef.current = null }
    const v = videoRef.current
    if (v) { v.removeAttribute('src'); v.srcObject = null; v.load() }
  }

  useEffect(() => {
    const video = videoRef.current
    if (!video || !stream) return
    setStatus(`Connecting via ${transport.toUpperCase()}…`)
    stopAll()

    if (transport === 'hls') {
      const url = stream.hls_url
      const playPromise = () => video.play().then(() => setPaused(false)).catch(() => { setPaused(true); setStatus('Tap Play to start (browser blocked autoplay)') })

      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url
        video.addEventListener('loadedmetadata', playPromise, { once: true })
      } else if (Hls.isSupported()) {
        const hls = new Hls({ liveDurationInfinity: true, lowLatencyMode: true, enableWorker: true })
        hlsRef.current = hls
        hls.loadSource(url)
        hls.attachMedia(video)
        hls.on(Hls.Events.MANIFEST_PARSED, () => { setStatus('Live (HLS)'); playPromise() })
        hls.on(Hls.Events.ERROR, (_e, data) => {
          if (!data.fatal) return
          setStatus(`HLS recover: ${data.details}`)
          // try to recover from network / media errors before giving up
          if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            reloadTimer.current = window.setTimeout(() => { setStatus('Reconnecting…'); hls.startLoad() }, 2000)
          } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
            hls.recoverMediaError()
          } else {
            setStatus(`HLS error: ${data.details} — try switching transport`)
          }
        })
      } else {
        setStatus('HLS not supported in this browser — use the direct link below')
      }
    } else {
      startWebRTC(stream.webrtc_url)
    }
    return stopAll
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream, transport])

  async function startWebRTC(url: string) {
    const video = videoRef.current!
    try {
      const pc = new RTCPeerConnection()
      pcRef.current = pc
      pc.addTransceiver('video', { direction: 'recvonly' })
      pc.ontrack = (ev) => { video.srcObject = ev.streams[0]; video.play().then(() => setPaused(false)).catch(() => {}) }
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      const res = await fetch(url, { method: 'POST', body: offer.sdp, headers: { 'Content-Type': 'application/sdp' } })
      if (!res.ok) { setStatus(`WebRTC unavailable (${res.status}) — build streamer with INSTALL_WEBRTC=true; using HLS`); setTransport('hls'); return }
      const answer = await res.text()
      await pc.setRemoteDescription({ sdp: answer, type: 'answer' })
      setStatus('Live (WebRTC · sub-second)')
    } catch (e: any) {
      setStatus(`WebRTC failed: ${e.message} — falling back to HLS`)
      setTransport('hls')
    }
  }

  const manualPlay = () => {
    const v = videoRef.current
    if (!v) return
    v.play().then(() => { setPaused(false); setStatus('Live (HLS)') }).catch((e) => setStatus(`Play blocked: ${e.message}`))
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Live View</h1>
      <div className="flex flex-wrap gap-2 items-center">
        <select value={selected} onChange={(e) => { setSelected(e.target.value); setParams({ cam: e.target.value }) }} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5 text-sm min-w-[18rem]">
          <option value="">Select a camera…</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>{c.id} — {c.name}{c.source_type === 'community' ? ' (community)' : ''}</option>
          ))}
        </select>
        <div className="flex bg-slate-900 border border-slate-800 rounded overflow-hidden text-sm">
          {(['hls', 'webrtc'] as Transport[]).map((t) => (
            <button key={t} onClick={() => setTransport(t)}
              className={`px-3 py-1.5 ${transport === t ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}>
              {t === 'hls' ? 'HLS' : 'WebRTC'}
            </button>
          ))}
        </div>
        {stream && <span className="text-xs text-slate-500">{stream.source_type === 'community' ? 'community camera · consent on file' : 'government camera'}</span>}
      </div>

      <div className="relative bg-black rounded-lg border border-slate-800 aspect-video max-w-3xl flex items-center justify-center">
        <video
          ref={videoRef}
          controls
          autoPlay
          muted
          playsInline
          onPlaying={() => { setPaused(false); setStatus('Live (HLS)') }}
          onWaiting={() => setStatus('Buffering…')}
          onError={() => setStatus('Video element error')}
          className="w-full h-full rounded-lg"
        />
        {paused && stream && (
          <button onClick={manualPlay} className="absolute inset-0 flex items-center justify-center bg-black/40 hover:bg-black/30">
            <span className="bg-brand-600 rounded-full w-16 h-16 flex items-center justify-center text-2xl">▶</span>
          </button>
        )}
      </div>
      <div className="text-xs text-slate-500">{status || (selected ? 'Ready.' : 'Select a camera to begin a live view.')}</div>
      {stream && (
        <div className="text-[11px] text-slate-600 flex flex-wrap items-center gap-2">
          <span>Direct link (Safari/Edge plays natively):</span>
          <a className="text-brand-400 hover:underline" href={stream.hls_url} target="_blank" rel="noreferrer">{stream.hls_url}</a>
          <span className="ml-2">· Streams pull on-demand; HLS works out of the box, WebRTC needs INSTALL_WEBRTC=true.</span>
        </div>
      )}
    </div>
  )
}
