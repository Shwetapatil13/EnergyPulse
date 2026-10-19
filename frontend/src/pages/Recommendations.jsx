import { useState, useEffect } from 'react'
import { Lightbulb, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react'
import { getRecommendations } from '../api'

const CONFIDENCE_COLORS = {
  'low — estimate only': 'var(--accent-yellow)',
  'informational': 'var(--accent-cyan)',
  'medium': 'var(--accent-green)',
  'high': 'var(--accent-green)',
}

const REC_ICONS = {
  peak_hours: '⏰',
  base_load: '🌙',
  weekday_weekend: '📅',
  sub_metering: '🔌',
}

function RecCard({ rec, index }) {
  const [expanded, setExpanded] = useState(false)
  const confColor = CONFIDENCE_COLORS[rec.confidence] || 'var(--text-muted)'
  const icon = REC_ICONS[rec.id] || '💡'

  return (
    <div className="rec-card" style={{ animationDelay: `${index * 60}ms` }}>
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{ fontSize: '1.4rem', flexShrink: 0, marginTop: 2 }}>{icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{rec.title}</div>
            <span style={{ fontSize: '0.65rem', color: confColor, background: `${confColor}18`, border: `1px solid ${confColor}40`, padding: '2px 8px', borderRadius: 20, fontWeight: 600, textTransform: 'uppercase' }}>
              {rec.confidence}
            </span>
            {rec.estimated_daily_saving_inr != null && (
              <span style={{ marginLeft: 'auto', background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: 'var(--accent-green)', fontSize: '0.78rem', fontWeight: 700, padding: '3px 10px', borderRadius: 20 }}>
                ~₹{rec.estimated_daily_saving_inr}/day
              </span>
            )}
          </div>

          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {rec.description}
          </div>

          <button className="btn btn-ghost" style={{ marginTop: 10, padding: '4px 12px', fontSize: '0.75rem' }}
            onClick={() => setExpanded(e => !e)}>
            {expanded ? '▲ Less' : '▼ Details & assumptions'}
          </button>

          {expanded && (
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8, animation: 'fadeIn 0.2s ease' }}>
              <div style={{ background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--accent-yellow)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>⚠ Assumptions</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{rec.assumption}</div>
              </div>
              <div style={{ background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.15)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>📊 Data source</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{rec.data_source}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Recommendations() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)

  const load = async () => {
    setLoading(true)
    setErr(null)
    try {
      const d = await getRecommendations()
      setData(d)
    } catch (e) {
      setErr('Failed to load recommendations.')
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const recs = data?.recommendations || []
  const withSavings = recs.filter(r => r.estimated_daily_saving_inr != null)
  const totalSavings = withSavings.reduce((s, r) => s + r.estimated_daily_saving_inr, 0)

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>💡 Recommendations</h1>
          <div className="section-sub">Data-derived energy efficiency suggestions</div>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      {/* Disclaimer */}
      <div style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, padding: '10px 16px', marginBottom: 20, fontSize: '0.78rem', color: '#f87171', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
        <span>
          <strong>Not financial advice.</strong> {data?.disclaimer || 'All savings are rough approximations based on dataset patterns. Verify against actual utility bills.'}
        </span>
      </div>

      {data && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 20, flexWrap: 'wrap' }}>
          <div className="stat-card" style={{ flex: '1 1 200px' }}>
            <div className="stat-label">Tariff Assumption</div>
            <div className="stat-value" style={{ color: 'var(--accent-cyan)', fontSize: '1.4rem' }}>
              ₹{data.tariff_assumption_inr_per_kwh}/kWh
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
              {data.tariff_note} Edit in Settings.
            </div>
          </div>
          {totalSavings > 0 && (
            <div className="stat-card" style={{ flex: '1 1 200px' }}>
              <div className="stat-label">Estimated Combined Saving</div>
              <div className="stat-value" style={{ color: 'var(--accent-green)', fontSize: '1.4rem' }}>
                ~₹{totalSavings.toFixed(2)}/day
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>Low confidence — estimate only</div>
            </div>
          )}
        </div>
      )}

      {loading
        ? <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
        : err
          ? <div className="card" style={{ color: 'var(--accent-red)', display: 'flex', gap: 10 }}>
              <AlertCircle size={18} /> {err}
            </div>
          : recs.length === 0
            ? <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: 40, color: 'var(--text-muted)' }}>
                <Lightbulb size={32} style={{ opacity: 0.3 }} />
                <div style={{ fontSize: '0.9rem' }}>No recommendations yet — start the simulator to accumulate data.</div>
              </div>
            : <div>
                {recs.map((r, i) => <RecCard key={r.id} rec={r} index={i} />)}
              </div>
      }
    </div>
  )
}
