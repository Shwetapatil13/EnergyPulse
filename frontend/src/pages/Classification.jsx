import { useState, useEffect } from 'react'
import {
  PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { Brain, Info, RefreshCw } from 'lucide-react'
import { getClassificationSummary, getModelMetrics } from '../api'

const LABEL_COLORS = {
  low: '#10b981',
  moderate: '#f59e0b',
  high: '#ef4444',
}

const CHART_TOOLTIP = {
  contentStyle: { background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
}

export default function Classification() {
  const [dist, setDist] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [d, m] = await Promise.all([getClassificationSummary(), getModelMetrics()])
      setDist(d.distribution || [])
      setMetrics(m)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const total = dist.reduce((s, r) => s + r.count, 0)

  const pieData = dist.map(r => ({
    name: r.label,
    value: r.count,
    fill: LABEL_COLORS[r.label] || '#8b5cf6',
  }))

  const barData = dist.map(r => ({
    label: r.label,
    avg_kw: +r.avg_kw.toFixed(4),
    count: r.count,
    pct: total > 0 ? +((r.count / total) * 100).toFixed(1) : 0,
  }))

  const classRuns = metrics?.model_runs?.filter(r => r.task === 'classification') || []

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>🧠 Load Classification</h1>
          <div className="section-sub">Percentile-based labeling · low / moderate / high</div>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      {/* Disclaimer */}
      <div style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 10, padding: '10px 16px', marginBottom: 20, fontSize: '0.78rem', color: 'var(--accent-purple)', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <Info size={15} style={{ flexShrink: 0, marginTop: 1 }} />
        <span>
          Labels are computed from percentile thresholds of the training data — <strong>not</strong> from a pre-trained appliance-detection model.
          {' '}low ≤ p33, moderate = p33–p67, high &gt; p67 of active power distribution.
        </span>
      </div>

      {loading ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
      ) : (
        <>
          <div className="grid-3" style={{ marginBottom: 20 }}>
            {dist.map(r => (
              <div key={r.label} className="stat-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div className="stat-label">{r.label?.toUpperCase()} consumption</div>
                    <div className="stat-value" style={{ color: LABEL_COLORS[r.label], fontSize: '1.8rem' }}>
                      {total > 0 ? ((r.count / total) * 100).toFixed(1) : 0}%
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>
                      {r.count.toLocaleString()} readings · avg {r.avg_kw.toFixed(3)} kW
                    </div>
                  </div>
                  <span className={`badge badge-${r.label}`}>{r.label}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="grid-2" style={{ marginBottom: 20 }}>
            {/* Pie chart */}
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>Distribution Breakdown</div>
              {pieData.length === 0
                ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No data — run simulator first</div>
                : <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                        paddingAngle={3} dataKey="value" nameKey="name">
                        {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                      </Pie>
                      <Tooltip {...CHART_TOOLTIP} formatter={(v) => [v.toLocaleString(), 'Readings']} />
                      <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }} />
                    </PieChart>
                  </ResponsiveContainer>
              }
            </div>

            {/* Bar chart: avg kW per class */}
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>Avg Power per Class</div>
              {barData.length === 0
                ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No data</div>
                : <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={barData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kW" />
                      <Tooltip {...CHART_TOOLTIP} />
                      <Bar dataKey="avg_kw" name="Avg Power (kW)" radius={[6, 6, 0, 0]}>
                        {barData.map((b, i) => <Cell key={i} fill={LABEL_COLORS[b.label] || '#8b5cf6'} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
              }
            </div>
          </div>

          {/* Model metrics */}
          {classRuns.length > 0 && (
            <div className="card">
              <div className="section-title" style={{ marginBottom: 16 }}>Trained Model Runs</div>
              <div style={{ overflowX: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Accuracy</th>
                      <th>F1 (weighted)</th>
                      <th>Train Rows</th>
                      <th>Test Rows</th>
                      <th>Trained At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {classRuns.map((r, i) => {
                      const m = typeof r.metrics === 'string' ? JSON.parse(r.metrics) : r.metrics || {}
                      return (
                        <tr key={i}>
                          <td className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem' }}>{r.model_name}</td>
                          <td className="mono">{m.accuracy != null ? (m.accuracy * 100).toFixed(1) + '%' : '—'}</td>
                          <td className="mono">{m.f1_weighted != null ? m.f1_weighted.toFixed(4) : '—'}</td>
                          <td className="mono">{(r.train_rows || 0).toLocaleString()}</td>
                          <td className="mono">{(r.test_rows || 0).toLocaleString()}</td>
                          <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.trained_at?.slice(0, 19) || '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 10 }}>
                {metrics?.note}
              </div>
            </div>
          )}

          {classRuns.length === 0 && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-muted)' }}>
              <Brain size={20} />
              <span style={{ fontSize: '0.85rem' }}>No trained classification models found. Run <code style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: 4 }}>python -m backend.app.ml.train_classifier</code> to train.</span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
