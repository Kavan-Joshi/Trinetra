const TOKEN_KEY = 'trinetra_token'
const ROLE_KEY = 'trinetra_role'
const NAME_KEY = 'trinetra_name'
const DEPT_KEY = 'trinetra_dept'

export const getToken = () => localStorage.getItem(TOKEN_KEY) ?? ''
export const getRole = () => localStorage.getItem(ROLE_KEY) ?? ''
export const getDisplayName = () => localStorage.getItem(NAME_KEY) ?? ''
export const getDepartmentId = () => localStorage.getItem(DEPT_KEY) ?? ''

export function setAuth(token: string, role: string, name: string, departmentId: number | null = null) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
  localStorage.setItem(NAME_KEY, name)
  if (departmentId !== null && departmentId !== undefined) localStorage.setItem(DEPT_KEY, String(departmentId))
  else localStorage.removeItem(DEPT_KEY)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(NAME_KEY)
  localStorage.removeItem(DEPT_KEY)
}

export async function api<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`
  if (opts.body) headers['Content-Type'] = 'application/json'
  const res = await fetch(path, { ...opts, headers })
  if (res.status === 401) {
    clearAuth()
    window.location.hash = '#/login'
    throw new Error('Session expired')
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(detail.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function fmtTime(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', { hour12: false })
}

export function normPlate(plate: string): string {
  return plate.replace(/[^A-Za-z0-9]/g, '').toUpperCase()
}

export const CATEGORY_STYLES: Record<string, string> = {
  stolen_vehicle: 'bg-red-500/15 text-red-300 border-red-500/40',
  blacklisted_vehicle: 'bg-orange-500/15 text-orange-300 border-orange-500/40',
  wanted_person: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40',
  missing_person: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  suspect: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  anomaly: 'bg-violet-500/15 text-violet-300 border-violet-500/40',
}

export const CATEGORY_LABELS: Record<string, string> = {
  stolen_vehicle: 'STOLEN VEHICLE',
  blacklisted_vehicle: 'BLACKLISTED',
  wanted_person: 'WANTED PERSON',
  missing_person: 'MISSING PERSON',
  suspect: 'SUSPECT',
  anomaly: 'ANOMALY',
}
