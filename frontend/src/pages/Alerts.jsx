import { useState, useEffect, useCallback } from 'react'
import { Bell, CheckCircle, Filter, Download, RefreshCw, AlertTriangle } from 'lucide-react'
import { getAlerts, getAlertSummary, acknowledgeAlert, exportAlertsCSV } from '../api'

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }
const SEV_COLORS = {
  critical: { bg: 'rgba(239,68,68,0.08)', border: '#ef4444', badge: 'badge-critical', icon: '🔴' },
  high: { bg: 'rgba(249,115,22,0.08)', border: '#f97316', badge: 'badge-high', icon: '🟠' },
  medium: { bg: 'rgba(245,158,11,0.08)', border: '#f59e0b', badge: 'badge-moderate', icon: '🟡' },
  low: { bg: 'rgba(59,130,246,0.08)', border: '#3b82f6', badge: 'badge-low', icon: '🔵' },
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [sevFilter, setSevFilter] = useState('')
  const [ackFilter, setAckFilter] = useState('')
  const [acking, setAcking] = useState(null)
  const PAGE_SIZE = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE }
      if (sevFilter) params.severity = sevFilter
      if (ackFilter !== '') params.acknowledged = ackFilter === 'true'
      const [a, s] = await Promise.all([getAlerts(params), getAlertSummary()])
      setAlerts(a.alerts || a || [])
      setTotal(a.total || (a.alerts || a || []).length)
      setSummary(s)
    } catch {}
    setLoading(false)
  }, [page, sevFilter, ackFilter])

  useEffect(() => { load() }, [load])

  const handleAck = async (id) => {
    setAcking(id)
    try {
      await acknowledgeAlert(id)
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a))
    } catch {}
    setAcking(null)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>🔔 Alerts</h1>
          <div className="section-sub">Anomaly detections and threshold violations</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /></button>
          <button className="btn btn-ghost" onClick={() => exportAlertsCSV({ severity: sevFilter })}>
            <Download size={14} /> Export
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid-4" style={{ marginBottom: 20 }}>
          {[
            { label: 'Total Alerts', value: summary.total || 0, color: 'var(--text-primary)' },
            { label: 'Critical / High', value: (summary.by_severity?.critical || 0) + (summary.by_severity?.high || 0), color: 'var(--accent-red)' },
            { label: 'Unacknowledged', value: summary.unacknowledged || 0, color: 'var(--accent-orange)' },
            { label: 'Last 24h', value: summary.last_24h || 0, color: 'var(--accent-yellow)' },
          ].map(c => (
            <div key={c.label} className="stat-card">
              <div className="stat-label">{c.label}</div>
              <div className="stat-value" style={{ color: c.color, fontSize: '1.6rem' }}>{c.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <Filter size={14} style={{ color: 'var(--text-muted)' }} />
        <select className="input" style={{ padding: '5px 10px', fontSize: '0.8rem', width: 130 }}
          value={sevFilter} onChange={e => { setSevFilter(e.target.value); setPage(1) }}>
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select className="input" style={{ padding: '5px 10px', fontSize: '0.8rem', width: 150 }}
          value={ackFilter} onChange={e => { setAckFilter(e.target.value); setPage(1) }}>
          <option value="">All status</option>
          <option value="false">Unacknowledged</option>
          <option value="true">Acknowledged</option>
        </select>
        {(sevFilter || ackFilter) && (
          <button className="btn btn-ghost" style={{ padding: '5px 10px', fontSize: '0.78rem' }}
            onClick={() => { setSevFilter(''); setAckFilter(''); setPage(1) }}>Clear filters</button>
        )}
        <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {total.toLocaleString()} total
        </span>
      </div>

      {/* Alert list */}
      {loading
        ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
        : alerts.length === 0
          ? <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '40px', color: 'var(--text-muted)' }}>
              <Bell size={32} style={{ opacity: 0.3 }} />
              <div style={{ fontSize: '0.9rem' }}>No alerts match the current filters.</div>
              <div style={{ fontSize: '0.78rem' }}>Alerts are generated during simulation when anomalies or threshold violations are detected.</div>
            </div>
          : <div style={{ marginBottom: 16 }}>
              {alerts.map(a => {
                const s = SEV_COLORS[a.severity?.toLowerCase()] || SEV_COLORS.low
                return (
                  <div key={a.id} className="alert-item" style={{ background: s.bg, borderLeftColor: s.border, opacity: a.acknowledged ? 0.55 : 1 }}>
                    <span style={{ fontSize: '1rem', flexShrink: 0 }}>{s.icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                          {(a.alert_type || '').replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <span className={`badge ${s.badge}`}>{a.severity}</span>
                        {a.acknowledged && <span className="badge badge-low" style={{ fontSize: '0.6rem' }}>✓ ACK</span>}
                        <span style={{ marginLeft: 'auto', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {new Date(a.timestamp).toLocaleString()}
                        </span>
                      </div>
                      {a.rule_description && (
                        <div style={{ fontSize: '0.77rem', color: 'var(--text-secondary)', marginTop: 4 }}>{a.rule_description}</div>
                      )}
                      {(a.value != null || a.threshold != null) && (
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
                          {a.value != null && <span>Value: <span className="mono">{a.value.toFixed(4)}</span></span>}
                          {a.threshold != null && <span style={{ marginLeft: 12 }}>Threshold: <span className="mono">{a.threshold.toFixed(4)}</span></span>}
                        </div>
                      )}
                    </div>
                    {!a.acknowledged && (
                      <button className="btn btn-ghost" disabled={acking === a.id}
                        style={{ padding: '4px 10px', fontSize: '0.75rem', flexShrink: 0 }}
                        onClick={() => handleAck(a.id)}>
                        <CheckCircle size={12} /> Ack
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
      }

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 8 }}>
          <button className="btn btn-ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
            {page} / {totalPages}
          </span>
          <button className="btn btn-ghost" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}
