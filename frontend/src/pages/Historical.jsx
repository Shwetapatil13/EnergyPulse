import { useState, useEffect, useCallback } from 'react'
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { Calendar, Download, RefreshCw, BarChart2, TrendingUp, Zap } from 'lucide-react'
import { getHourlyAgg, getDailyAgg, getHeatmap, exportReadingsCSV } from '../api'
import api from '../api'

const CHART_TOOLTIP = {
  contentStyle: { background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function SummaryCard({ label, value, sub, color = 'var(--accent-blue)' }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color, fontSize: '1.5rem' }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function LoadingBox({ height = 220 }) {
  return (
    <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="spinner" />
    </div>
  )
}

function EmptyState({ text = 'No data yet' }) {
  return (
    <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', flexDirection: 'column', gap: 8 }}>
      <BarChart2 size={28} style={{ opacity: 0.3 }} />
      <span style={{ fontSize: '0.85rem' }}>{text}</span>
    </div>
  )
}

export default function Historical() {
  const [tab, setTab] = useState('hourly')
  const [summary, setSummary] = useState(null)
  const [hourly, setHourly] = useState([])
  const [daily, setDaily] = useState([])
  const [heatmap, setHeatmap] = useState(null)
  const [loading, setLoading] = useState(true)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [downloading, setDownloading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (startDate) params.start = startDate
      if (endDate) params.end = endDate

      const [summaryRes, hourlyRes, dailyRes] = await Promise.all([
        api.get('/api/readings/summary', { params }).then(r => r.data),
        api.get('/api/aggregates/hourly', { params: { ...params, limit: 500 } }).then(r => r.data),
        api.get('/api/aggregates/daily', { params: { ...params, limit: 1500 } }).then(r => r.data),
      ])

      setSummary(summaryRes)
      // API returns array directly — map timestamp -> label
      setHourly((Array.isArray(hourlyRes) ? hourlyRes : []).map(r => ({
        ...r,
        label: new Date(r.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' }),
      })))
      setDaily((Array.isArray(dailyRes) ? dailyRes : []).map(r => ({
        ...r,
        label: r.date ? r.date.slice(0, 10) : '',
      })))
    } catch (e) {
      console.error('Historical load error', e)
    }
    setLoading(false)
  }, [startDate, endDate])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    getHeatmap().then(r => setHeatmap(r)).catch(() => {})
  }, [])

  const handleExportCSV = async () => {
    setDownloading(true)
    try {
      const params = {}
      if (startDate) params.start = startDate
      if (endDate) params.end = endDate
      const res = await api.get('/api/readings/export/csv', { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `energypulse_readings${startDate ? '_' + startDate : ''}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      alert('CSV export failed. Make sure the backend is running.')
    }
    setDownloading(false)
  }

  // Derived summary values (API field names)
  const totalReadings = summary?.count ? Math.round(summary.count).toLocaleString() : '—'
  const totalEnergy = summary?.total_energy_kwh ? `${(summary.total_energy_kwh).toFixed(1)} kWh` : '—'
  const avgPower = summary?.avg_power_kw ? `${summary.avg_power_kw.toFixed(3)} kW` : '—'
  const peakPower = summary?.peak_power_kw ? `${summary.peak_power_kw.toFixed(3)} kW` : '—'

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>📊 Historical Analysis</h1>
          <div className="section-sub">Full dataset 2006–2010 · UCI Household Power Consumption</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input className="input" type="date" style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            min="2006-12-16" max="2010-11-26" value={startDate}
            onChange={e => setStartDate(e.target.value)} />
          <input className="input" type="date" style={{ padding: '5px 10px', fontSize: '0.8rem' }}
            min="2006-12-16" max="2010-11-26" value={endDate}
            onChange={e => setEndDate(e.target.value)} />
          <button className="btn btn-ghost" onClick={load} title="Refresh"><RefreshCw size={14} /></button>
          <button className="btn btn-primary" onClick={handleExportCSV} disabled={downloading}>
            <Download size={14} /> {downloading ? 'Downloading…' : 'Export CSV'}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <SummaryCard label="Total Readings" color="var(--accent-purple)"
          value={totalReadings} sub="1-min intervals" />
        <SummaryCard label="Total Energy" color="var(--accent-cyan)"
          value={totalEnergy} sub="Entire dataset" />
        <SummaryCard label="Avg Active Power" color="var(--accent-blue)"
          value={avgPower} />
        <SummaryCard label="Peak Power" color="var(--accent-orange)"
          value={peakPower} sub="Max recorded" />
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {[['hourly', 'Hourly Trend', BarChart2], ['daily', 'Daily Trend', Calendar], ['heatmap', 'Heatmap', Zap]].map(([id, label, Icon]) => (
          <button key={id} className={`btn ${tab === id ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setTab(id)} style={{ fontSize: '0.82rem' }}>
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {/* Hourly chart */}
      {tab === 'hourly' && (
        <div className="card">
          <div className="section-header">
            <div className="section-title">Avg Power (kW) — Hourly</div>
            <div className="section-sub">Last {Math.min(hourly.length, 500)} hourly records</div>
          </div>
          {loading ? <LoadingBox /> : hourly.length === 0
            ? <EmptyState text="No hourly data — run the simulator or reload" />
            : <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={hourly} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="gHourly" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kW" />
                  <Tooltip {...CHART_TOOLTIP} formatter={(v) => [v?.toFixed(4) + ' kW', 'Avg Power']} />
                  <Area type="monotone" dataKey="avg_power_kw" name="Avg Power (kW)"
                    stroke="#06b6d4" fill="url(#gHourly)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
          }
        </div>
      )}

      {/* Daily chart */}
      {tab === 'daily' && (
        <div className="card">
          <div className="section-header">
            <div className="section-title">Avg Power (kW) — Daily</div>
            <div className="section-sub">{daily.length} days of data</div>
          </div>
          {loading ? <LoadingBox /> : daily.length === 0
            ? <EmptyState />
            : <ResponsiveContainer width="100%" height={280}>
                <BarChart data={daily} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kW" />
                  <Tooltip {...CHART_TOOLTIP} formatter={(v) => [v?.toFixed(4) + ' kW', 'Avg Power']} />
                  <Bar dataKey="avg_power_kw" name="Avg Power (kW)" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
          }

          {/* Also show max/min table */}
          {!loading && daily.length > 0 && (
            <div style={{ marginTop: 16, overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Avg kW</th>
                    <th>Max kW</th>
                    <th>Min kW</th>
                    <th>Load Factor</th>
                    <th>Day</th>
                  </tr>
                </thead>
                <tbody>
                  {daily.slice(-15).reverse().map((d, i) => (
                    <tr key={i}>
                      <td className="mono" style={{ fontSize: '0.78rem' }}>{d.label}</td>
                      <td className="mono">{d.avg_power_kw?.toFixed(3) ?? '—'}</td>
                      <td className="mono">{d.max_power_kw?.toFixed(3) ?? '—'}</td>
                      <td className="mono">{d.min_power_kw?.toFixed(3) ?? '—'}</td>
                      <td className="mono">{d.load_factor ? (d.load_factor * 100).toFixed(1) + '%' : '—'}</td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        {d.day_of_week != null ? DAYS[d.day_of_week] : '—'}
                        {d.is_weekend ? ' 🏖️' : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Heatmap */}
      {tab === 'heatmap' && (
        <div className="card">
          <div className="section-header">
            <div>
              <div className="section-title">Hour × Day-of-Week Heatmap</div>
              <div className="section-sub">Average active power (kW) — 4 years of data</div>
            </div>
          </div>
          {!heatmap
            ? <LoadingBox />
            : <HeatmapGrid data={heatmap} />
          }
        </div>
      )}
    </div>
  )
}

function HeatmapGrid({ data }) {
  const flatRows = data?.heatmap || []
  if (flatRows.length === 0) return <EmptyState text="No heatmap data" />

  // Build 7×24 matrix: grid[dow][hour] = avg_kw  (dow: 1=Sun...7=Sat in MySQL)
  const matrix = {}
  let maxVal = 0
  flatRows.forEach(r => {
    if (!matrix[r.dow]) matrix[r.dow] = {}
    matrix[r.dow][r.hour] = r.avg_kw
    if (r.avg_kw > maxVal) maxVal = r.avg_kw
  })
  maxVal = maxVal || 1

  const dowOrder = [1, 2, 3, 4, 5, 6, 7]
  const dowLabels = { 1: 'Sun', 2: 'Mon', 3: 'Tue', 4: 'Wed', 5: 'Thu', 6: 'Fri', 7: 'Sat' }

  return (
    <div style={{ overflowX: 'auto' }}>
      <div style={{ display: 'inline-grid', gridTemplateColumns: '44px repeat(24, 30px)', gap: '3px', minWidth: 'max-content' }}>
        {/* Header row */}
        <div />
        {Array.from({ length: 24 }, (_, i) => (
          <div key={i} style={{ fontSize: '0.58rem', color: 'var(--text-muted)', textAlign: 'center', paddingBottom: 4, fontWeight: 600 }}>
            {i}h
          </div>
        ))}

        {/* Data rows */}
        {dowOrder.map(dow => (
          <>
            <div key={`lbl-${dow}`} style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 6, fontWeight: 600 }}>
              {dowLabels[dow]}
            </div>
            {Array.from({ length: 24 }, (_, h) => {
              const val = matrix[dow]?.[h] || 0
              const t = val / maxVal
              const bg = `rgba(${Math.round(59 + t * 196)}, ${Math.round(130 - t * 100)}, ${Math.round(246 - t * 220)}, ${0.12 + t * 0.75})`
              return (
                <div key={`${dow}-${h}`} className="heatmap-cell"
                  style={{ background: bg, width: 30, height: 30 }}
                  title={`${dowLabels[dow]} ${h}:00 → ${val.toFixed(3)} kW`} />
              )
            })}
          </>
        ))}
      </div>

      {/* Legend */}
      <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
        <span>Low</span>
        {[0.1, 0.3, 0.5, 0.7, 0.9, 1.0].map(t => (
          <div key={t} style={{ width: 22, height: 14, borderRadius: 3, background: `rgba(${Math.round(59 + t * 196)}, ${Math.round(130 - t * 100)}, ${Math.round(246 - t * 220)}, ${0.12 + t * 0.75})` }} />
        ))}
        <span>High ({(maxVal).toFixed(2)} kW)</span>
      </div>
    </div>
  )
}
