import { useState } from 'react'
import { api } from '../api'

export default function CommunityPage() {
  const [form, setForm] = useState({
    id: 'COMM-010', name: '', lat: 23.03, lon: 72.53,
    stream_url: 'rtsp://', owner_name: '', owner_contact: '', notes: '', consent: true,
  })
  const [msg, setMsg] = useState('')

  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async () => {
    setMsg('')
    try {
      const r = await api('/api/v1/community/cameras', { method: 'POST', body: JSON.stringify(form) })
      setMsg(`Onboarded ${r.id} as a community camera (consent recorded).`)
    } catch (e: any) {
      setMsg(e.message)
    }
  }

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold">Community Camera Onboarding</h1>
        <p className="text-xs text-slate-500 mt-1">
          Self-service onboarding for public-facing CCTV cameras installed by societies, malls and commercial
          establishments. Feeds appear in the registry with a restricted scope and explicit consent on file.
        </p>
      </div>
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 grid grid-cols-2 gap-3">
        <Field label="Camera ID"><input value={form.id} onChange={(e) => set('id', e.target.value)} className={inp} /></Field>
        <Field label="Location name"><input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="e.g. Sunrise Society Gate" className={inp} /></Field>
        <Field label="Latitude"><input type="number" step="0.0001" value={form.lat} onChange={(e) => set('lat', parseFloat(e.target.value))} className={inp} /></Field>
        <Field label="Longitude"><input type="number" step="0.0001" value={form.lon} onChange={(e) => set('lon', parseFloat(e.target.value))} className={inp} /></Field>
        <Field label="RTSP / stream URL" full><input value={form.stream_url} onChange={(e) => set('stream_url', e.target.value)} className={inp} /></Field>
        <Field label="Owner name"><input value={form.owner_name} onChange={(e) => set('owner_name', e.target.value)} className={inp} /></Field>
        <Field label="Owner contact"><input value={form.owner_contact} onChange={(e) => set('owner_contact', e.target.value)} className={inp} /></Field>
        <Field label="Notes" full><input value={form.notes} onChange={(e) => set('notes', e.target.value)} className={inp} /></Field>
        <label className="col-span-2 flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={form.consent} onChange={(e) => set('consent', e.target.checked)} />
          I confirm consent to share this public-facing feed with the State CCTV integration platform.
        </label>
        <button onClick={submit} disabled={!form.consent} className="col-span-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded py-2 text-sm font-medium">
          Onboard community camera
        </button>
        {msg && <div className="col-span-2 text-xs text-brand-300">{msg}</div>}
      </div>
    </div>
  )
}

const inp = 'w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm'

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className={full ? 'col-span-2' : ''}>
      <label className="text-xs text-slate-500">{label}</label>
      {children}
    </div>
  )
}
