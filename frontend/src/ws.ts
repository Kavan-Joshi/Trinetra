import { getToken } from './api'

export function connectAlerts(onAlert: (alert: any) => void): () => void {
  let closed = false
  let ws: WebSocket | null = null

  const connect = () => {
    const token = getToken()
    if (!token) {
      setTimeout(connect, 2000)
      return
    }
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    ws = new WebSocket(`${proto}://${window.location.host}/ws/alerts?token=${token}`)
    ws.onmessage = (e) => {
      try {
        onAlert(JSON.parse(e.data))
      } catch {
        /* ignore malformed frame */
      }
    }
    ws.onclose = () => {
      if (!closed) setTimeout(connect, 3000)
    }
    ws.onerror = () => ws?.close()
  }

  connect()
  return () => {
    closed = true
    ws?.close()
  }
}
