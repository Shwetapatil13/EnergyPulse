import { useState, useEffect, useCallback } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Download, RefreshCw } from 'lucide-react'
import { exportReadingsCSV, exportAlertsCSV } from '../api'
import api from '../api'

const CHART_TOOLTIP = {
  contentStyle: { background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
}
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export default function Reports() {
  const [summary, setSummary] = useState(null)
  const [daily, setDaily] = useState([])
  const [alertSummary, setAlertSummary] = useState(null)
  const [classSummary, setClassSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [dlReading, setDlReading] = useState(false)
  const [dlAlerts, setDlAlerts] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (startDate) params.start = startDate
      if (endDate) params.end = endDate
      const [s, d, a, c] = await Promise.all([
        api.get('/api/readings/summary', { params }).then(r => r.data),
        api.get('/api/aggregates/daily', { params: { ...params, limit: 1500 } }).then(r => r.data),
        api.get('/api/alerts/summary').then(r => r.data),
        api.get('/api/ml/classification/summary', { params }).then(r => r.data),
      ])
      setSummary(s)
      setDaily((Array.isArray(d) ? d : []).map(r => ({
        ...r,
        label: r.date ? r.date.slice(0, 10) : '',
      })))
      setAlertSummary(a)
      setClassSummary(c)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [startDate, endDate])

  useEffect(() => { load() }, [load])

  const handleExportReadings = async () => {
    setDlReading(true)
    try { await exportReadingsCSV({ start: startDate, end: endDate }) } catch { alert('Export failed') }
    setDlReading(false)
  }
  const handleExportAlerts = async () => {
    setDlAlerts(true)
    try { await exportAlertsCSV({}) } catch { alert('Export failed') }
    setDlAlerts(false)
  }

  const totalReadings = summary?.count ? Math.round(summary.count).toLocaleString() : '—'
  const totalEnergy = summary?.total_energy_kwh ? `${summary.total_energy_kwh.toFixed(1)} kWh` : '—'
  const totalCost = summary?.total_cost_inr ? `₹${summary.total_cost_inr.toFixed(0)}` : '—'
  const peakPower = summary?.peak_power_kw ? `${summary.peak_power_kw.toFixed(3)} kW` : '—'

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>📄 Reports</h1>
          <div className="section-sub">Summary statistics and data exports</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input className="input" type="date" style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            min="2006-12-16" max="2010-11-26" value={startDate} onChange={e => setStartDate(e.target.value)} />
          <input className="input" type="date" style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            min="2006-12-16" max="2010-11-26" value={endDate} onChange={e => setEndDate(e.target.value)} />
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /></button>
        </div>
      </div>

      {/* Export buttons */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleExportReadings} disabled={dlReading}>
          <Download size={14} /> {dlReading ? 'Downloading…' : 'Export Readings CSV'}
        </button>
        <button className="btn btn-ghost" onClick={handleExportAlerts} disabled={dlAlerts}>
          <Download size={14} /> {dlAlerts ? 'Downloading…' : 'Export Alerts CSV'}
        </button>
      </div>

      {loading
        ? <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
        : <>
            {/* KPI cards */}
            <div className="grid-4" style={{ marginBottom: 20 }}>
              <div className="stat-card">
                <div className="stat-label">Total Readings</div>
                <div className="stat-value" style={{ color: 'var(--accent-blue)', fontSize: '1.5rem' }}>{totalReadings}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>1-minute intervals</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Energy</div>
                <div className="stat-value" style={{ color: 'var(--accent-cyan)', fontSize: '1.5rem' }}>{totalEnergy}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Est. Cost</div>
                <div className="stat-value" style={{ color: 'var(--accent-green)', fontSize: '1.5rem' }}>{totalCost}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>@ ₹8/kWh assumed</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Peak Power</div>
                <div className="stat-value" style={{ color: 'var(--accent-orange)', fontSize: '1.5rem' }}>{peakPower}</div>
              </div>
            </div>

            {/* Daily bar chart */}
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="section-header">
                <div className="section-title">Daily Avg Power Trend</div>
                <div className="section-sub">{daily.length} days · last 30 shown</div>
              </div>
              {daily.length === 0
                ? <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No data</div>
                : <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={daily.slice(-30)} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} interval="preserveStartEnd" />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kW" />
                      <Tooltip {...CHART_TOOLTIP} formatter={(v) => [v?.toFixed(4) + ' kW', 'Avg Power']} />
                      <Bar dataKey="avg_power_kw" name="Avg Power (kW)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
              }
            </div>

            <div className="grid-2" style={{ marginBottom: 20 }}>
              {/* Alert breakdown */}
              <div className="card">
                <div className="section-title" style={{ marginBottom: 16 }}>Alert Breakdown</div>
                {!alertSummary || alertSummary.total === 0
                  ? <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No alerts yet — run the simulator to generate alerts.</div>
                  : <table className="table">
                      <thead><tr><th>Severity</th><th>Count</th><th>Share</th></tr></thead>
                      <tbody>
                        {Object.entries(alertSummary.by_severity || {}).sort((a, b) => b[1] - a[1]).map(([sev, cnt]) => (
                          <tr key={sev}>
                            <td><span className={`badge badge-${sev}`}>{sev}</span></td>
                            <td className="mono">{cnt.toLocaleString()}</td>
                            <td className="mono">{alertSummary.total ? ((cnt / alertSummary.total) * 100).toFixed(1) : 0}%</td>
                          </tr>
                        ))}
                        <tr style={{ borderTop: '2px solid var(--border)' }}>
                          <td style={{ fontWeight: 600 }}>Total</td>
                          <td className="mono" style={{ fontWeight: 600 }}>{(alertSummary.total || 0).toLocaleString()}</td>
                          <td className="mono">100%</td>
                        </tr>
                      </tbody>
                    </table>
                }
              </div>

              {/* Classification breakdown */}
              <div className="card">
                <div className="section-title" style={{ marginBottom: 16 }}>Load Classification</div>
                {!classSummary || classSummary.distribution?.length === 0
                  ? <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No classification data.</div>
                  : (() => {
                      const total = classSummary.distribution.reduce((s, r) => s + r.count, 0)
                      return (
                        <table className="table">
                          <thead><tr><th>Class</th><th>Readings</th><th>Avg kW</th><th>Share</th></tr></thead>
                          <tbody>
                            {classSummary.distribution.map(r => (
                              <tr key={r.label}>
                                <td><span className={`badge badge-${r.label}`}>{r.label}</span></td>
                                <td className="mono">{r.count.toLocaleString()}</td>
                                <td className="mono">{r.avg_kw?.toFixed(4)}</td>
                                <td className="mono">{total > 0 ? ((r.count / total) * 100).toFixed(1) : 0}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )
                    })()
                }
              </div>
            </div>

            {/* Disclaimer */}
            <div style={{ background: 'rgba(139,92,246,0.07)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 10, padding: '12px 16px', fontSize: '0.78rem', color: 'var(--accent-purple)' }}>
              🔬 <strong>Simulation only.</strong> All data from UCI Household Power Consumption dataset (2006–2010). Cost @ assumed ₹8/kWh flat rate.
            </div>
          </>
      }
    </div>
  )
}
