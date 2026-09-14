import { useState } from 'react'
import { api, normPlate } from '../api'

export default function RecordsPage() {
  const [plate, setPlate] = useState('')
  const [person, setPerson] = useState('')
  const [plateResult, setPlateResult] = useState<any | null>(null)
  const [personResult, setPersonResult] = useState<any | null>(null)
  const [busy, setBusy] = useState(false)

  const searchPlate = async () => {
    setBusy(true)
    setPlateResult(null)
    try {
      setPlateResult(await api(`/api/v1/records/plate/${normPlate(plate)}`))
    } catch { setPlateResult({ error: 'lookup failed' }) }
    finally { setBusy(false) }
  }

  const searchPerson = async () => {
    setBusy(true)
    setPersonResult(null)
    try {
      setPersonResult(await api(`/api/v1/records/person?name=${encodeURIComponent(person)}`))
    } catch { setPersonResult({ error: 'lookup failed' }) }
    finally { setBusy(false) }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Government Records Lookup</h1>
        <p className="text-xs text-slate-500 mt-1">
          Federated query across VAHAN, SARTHI, eGujCop (CCTNS) and NAFIS. Mock-backed for the demo;
          real connectors drop in behind the same interface.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="font-medium text-sm">Vehicle / plate dossier</div>
          <div className="flex gap-2">
            <input value={plate} onChange={(e) => setPlate(e.target.value)} placeholder="GJ-01-KA-1234"
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
            <button onClick={searchPlate} disabled={busy} className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded px-4 py-1.5 text-sm">Query</button>
          </div>
          {plateResult && !plateResult.error && (
            <div className="space-y-2 text-sm">
              <Row label="Plate" value={plateResult.plate_display} />
              {plateResult.vahan ? (
                <div className="border border-slate-800 rounded p-2 space-y-1">
                  <div className="text-[10px] uppercase text-sky-400">VAHAN</div>
                  <Row label="Owner" value={plateResult.vahan.owner_name} />
                  <Row label="Vehicle" value={`${plateResult.vahan.make} ${plateResult.vahan.model} (${plateResult.vahan.color})`} />
                  <Row label="Class" value={plateResult.vahan.vehicle_class} />
                  <Row label="Fitness" value={plateResult.vahan.fitness_expiry} />
                  <Row label="Insurance" value={plateResult.vahan.insurance_valid ? 'valid' : 'LAPSED'} highlight={!plateResult.vahan.insurance_valid} />
                </div>
              ) : <Muted text="No VAHAN record" />}
              {plateResult.cctns ? (
                <div className="border border-red-500/30 rounded p-2 space-y-1">
                  <div className="text-[10px] uppercase text-red-400">eGujCop / CCTNS</div>
                  <Row label="Category" value={plateResult.cctns.category?.replace('_', ' ')} />
                  <Row label="FIR ref" value={plateResult.cctns.source_ref} />
                  <Row label="Description" value={plateResult.cctns.description} />
                </div>
              ) : <Muted text="No CCTNS hit (not watchlisted)" />}
              {plateResult.sarathi && (
                <div className="border border-slate-800 rounded p-2 space-y-1">
                  <div className="text-[10px] uppercase text-teal-400">SARTHI (DL)</div>
                  <Row label="DL number" value={plateResult.sarathi.dl_number} />
                  <Row label="DL status" value={plateResult.sarathi.valid ? 'valid' : 'INVALID'} highlight={!plateResult.sarathi.valid} />
                </div>
              )}
            </div>
          )}
          {plateResult?.error && <Muted text={plateResult.error} />}
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
          <div className="font-medium text-sm">Person dossier</div>
          <div className="flex gap-2">
            <input value={person} onChange={(e) => setPerson(e.target.value)} placeholder="Person name"
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
            <button onClick={searchPerson} disabled={busy} className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded px-4 py-1.5 text-sm">Query</button>
          </div>
          {personResult && !personResult.error && (
            <div className="space-y-2 text-sm">
              {personResult.cctns ? (
                <div className="border border-red-500/30 rounded p-2 space-y-1">
                  <div className="text-[10px] uppercase text-red-400">eGujCop / CCTNS</div>
                  <Row label="Name" value={personResult.cctns.person_name} />
                  <Row label="Category" value={personResult.cctns.category?.replace('_', ' ')} />
                  <Row label="FIR ref" value={personResult.cctns.fir_ref} />
                  <Row label="Description" value={personResult.cctns.description} />
                </div>
              ) : <Muted text="No CCTNS person record" />}
              {personResult.nafis && personResult.nafis.matched && (
                <div className="border border-fuchsia-500/30 rounded p-2 space-y-1">
                  <div className="text-[10px] uppercase text-fuchsia-400">NAFIS (fingerprint)</div>
                  <Row label="Match" value={`YES · score ${(personResult.nafis.score * 100).toFixed(0)}%`} highlight />
                  <Row label="FIR ref" value={personResult.nafis.fir_ref} />
                </div>
              )}
              {personResult.nafis && !personResult.nafis.matched && <Muted text="No NAFIS fingerprint match" />}
            </div>
          )}
          {personResult?.error && <Muted text={personResult.error} />}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, highlight }: { label: string; value?: any; highlight?: boolean }) {
  if (value === null || value === undefined || value === '') return null
  return (
    <div className="flex gap-2 text-xs">
      <span className="text-slate-500 w-20 shrink-0">{label}</span>
      <span className={highlight ? 'text-red-300 font-medium' : 'text-slate-300'}>{String(value)}</span>
    </div>
  )
}

function Muted({ text }: { text: string }) {
  return <div className="text-xs text-slate-600 italic">{text}</div>
}
