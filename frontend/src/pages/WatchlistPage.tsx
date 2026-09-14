import { useCallback, useEffect, useState } from 'react'
import { api, fmtTime, getRole } from '../api'

const CATEGORIES = ['stolen_vehicle', 'blacklisted_vehicle', 'wanted_person', 'missing_person', 'suspect']

export default function WatchlistPage() {
  const [items, setItems] = useState<any[]>([])
  const [category, setCategory] = useState('stolen_vehicle')
  const [plate, setPlate] = useState('')
  const [personName, setPersonName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState('')
  const [model, setModel] = useState('')
  const [csvText, setCsvText] = useState('')
  const [msg, setMsg] = useState('')
  const canManage = ['admin', 'analyst'].includes(getRole())

  const load = useCallback(() => {
    api('/api/v1/watchlist?limit=200').then((r) => setItems(r.items)).catch(() => {})
  }, [])

  useEffect(load, [load])

  const add = async () => {
    setMsg('')
    try {
      await api('/api/v1/watchlist', {
        method: 'POST',
        body: JSON.stringify({ category, plate: plate || null, person_name: personName || null, description, color: color || null, model: model || null }),
      })
      setPlate(''); setPersonName(''); setDescription(''); setColor(''); setModel('')
      setMsg('Entry added.')
      load()
    } catch (e: any) {
      setMsg(e.message)
    }
  }

  const importCsv = async () => {
    setMsg('')
    try {
      const r = await api('/api/v1/watchlist/import', { method: 'POST', headers: { 'Content-Type': 'text/csv' }, body: csvText })
      setMsg(`Imported ${r.imported}, skipped ${r.skipped}.`)
      setCsvText('')
      load()
    } catch (e: any) {
      setMsg(e.message)
    }
  }

  const deactivate = async (id: number) => {
    await api(`/api/v1/watchlist/${id}`, { method: 'DELETE' })
    load()
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Watchlist Database</h1>

      {canManage && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="font-medium text-sm">Add entry</div>
            <div className="grid grid-cols-2 gap-3">
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm">
                {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
              </select>
              <input value={plate} onChange={(e) => setPlate(e.target.value)} placeholder="Plate (vehicles)" className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
              <input value={personName} onChange={(e) => setPersonName(e.target.value)} placeholder="Person name (persons)" className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
              <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="Vehicle model" className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
              <input value={color} onChange={(e) => setColor(e.target.value)} placeholder="Color" className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
              <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description / FIR ref" className="bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-sm" />
            </div>
            <button onClick={add} className="bg-brand-600 hover:bg-brand-500 rounded px-4 py-1.5 text-sm">Add to watchlist</button>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="font-medium text-sm">Bulk import (CSV)</div>
            <textarea
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              rows={5}
              placeholder={'category,plate,person_name,description,color,model\nstolen_vehicle,GJ-05-XX-1111,,Stolen from Adajan,White,Hyundai i20'}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-xs font-mono"
            />
            <button onClick={importCsv} className="border border-slate-700 hover:border-slate-500 rounded px-4 py-1.5 text-sm">Import CSV</button>
          </div>
        </div>
      )}
      {msg && <div className="text-xs text-brand-300">{msg}</div>}

      <div className="overflow-auto border border-slate-800 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-slate-500 text-xs uppercase">
            <tr>
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Category</th>
              <th className="p-2 text-left">Plate / Person</th>
              <th className="p-2 text-left">Vehicle</th>
              <th className="p-2 text-left">Source</th>
              <th className="p-2 text-left">Description</th>
              <th className="p-2 text-left">Added</th>
              <th className="p-2 text-left">Status</th>
              {canManage && <th className="p-2 text-left">Action</th>}
            </tr>
          </thead>
          <tbody>
            {items.map((w) => (
              <tr key={w.id} className="border-t border-slate-800/70 hover:bg-slate-900/50">
                <td className="p-2 text-slate-500">{w.id}</td>
                <td className="p-2 text-slate-300">{w.category.replace('_', ' ')}</td>
                <td className="p-2 font-medium text-brand-300">{w.plate ?? w.person_name ?? '—'}</td>
                <td className="p-2 text-slate-400">{[w.color, w.model].filter(Boolean).join(' ') || '—'}</td>
                <td className="p-2">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    w.source_system === 'manual' ? 'bg-slate-800 text-slate-400 border-slate-700'
                    : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                  }`}>
                    {w.source_system}{w.source_ref ? ` · ${w.source_ref}` : ''}
                  </span>
                </td>
                <td className="p-2 text-slate-400 max-w-xs truncate">{w.description || '—'}</td>
                <td className="p-2 text-slate-500 whitespace-nowrap">{w.created_at ? fmtTime(w.created_at) : '—'}</td>
                <td className="p-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded border ${w.active ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-slate-800 text-slate-500 border-slate-700'}`}>
                    {w.active ? 'active' : 'inactive'}
                  </span>
                </td>
                {canManage && (
                  <td className="p-2">
                    {w.active && (
                      <button onClick={() => deactivate(w.id)} className="text-xs text-red-300 border border-red-500/40 rounded px-2 py-1 hover:text-red-200">
                        Deactivate
                      </button>
                    )}
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
