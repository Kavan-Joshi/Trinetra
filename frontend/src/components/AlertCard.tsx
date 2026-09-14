import { CATEGORY_LABELS, CATEGORY_STYLES, fmtTime } from '../api'

const SOURCE_STYLES: Record<string, string> = {
  cctns: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  vahan: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  nafis: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40',
  manual: 'bg-slate-800 text-slate-400 border-slate-700',
}

export default function AlertCard({ alert, onTrack }: { alert: any; onTrack?: (plate: string) => void }) {
  const vahan = alert.enrichment?.vahan
  const source = alert.source_system || 'manual'
  return (
    <div className="flex gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition-colors">
      {alert.snapshot_path ? (
        <img
          src={`/evidence/${alert.snapshot_path}`}
          alt="evidence"
          className="w-32 h-[4.5rem] object-cover rounded border border-slate-800 shrink-0"
        />
      ) : (
        <div className="w-32 h-[4.5rem] rounded border border-slate-800 shrink-0 bg-slate-950 flex items-center justify-center text-slate-700 text-xs">
          no frame
        </div>
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${CATEGORY_STYLES[alert.category] || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
              {CATEGORY_LABELS[alert.category] || alert.category}
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${SOURCE_STYLES[source] || SOURCE_STYLES.manual}`}>
              {source.toUpperCase()}{alert.source_ref ? ` · ${alert.source_ref}` : ''}
            </span>
          </div>
          <span className="text-[10px] text-slate-500">{fmtTime(alert.ts)}</span>
        </div>
        <div className="text-sm font-medium text-slate-200 truncate mt-1">{alert.title}</div>
        <div className="text-xs text-slate-500">
          {alert.camera_id} · confidence {(alert.confidence * 100).toFixed(0)}%
          {alert.plate ? ` · ${alert.plate}` : ''}
          {alert.status && alert.status !== 'new' ? ` · ${alert.status.toUpperCase()}` : ''}
        </div>
        {vahan && (
          <div className="text-[11px] text-sky-300/80 mt-0.5 truncate">
            VAHAN: {vahan.owner_name ?? '—'} · {vahan.make} {vahan.model} · {vahan.color ?? '?'}
            {vahan.insurance_valid === false ? ' · insurance LAPSED' : ''}
          </div>
        )}
      </div>
      {alert.plate && onTrack && (
        <button
          onClick={() => onTrack(alert.plate)}
          className="self-center text-xs text-brand-400 hover:text-brand-300 border border-brand-500/40 rounded px-2 py-1 shrink-0"
        >
          Track
        </button>
      )}
    </div>
  )
}
