import { useState, useEffect } from 'react'
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine
} from 'recharts'
import { TrendingUp, Info, RefreshCw } from 'lucide-react'
import { getForecast, getForecastVsActual, getModelMetrics } from '../api'

const CHART_TOOLTIP = {
  contentStyle: { background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: 'var(--text-secondary)', fontSize: 11 },
}

export default function Forecast() {
  const [hours, setHours] = useState(24)
  const [forecast, setForecast] = useState(null)
  const [vsActual, setVsActual] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [f, va, m] = await Promise.all([getForecast(hours), getForecastVsActual(), getModelMetrics()])
      setForecast(f)
      setVsActual(va.data || [])
      setMetrics(m)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [hours])

  const forecastPoints = forecast?.predictions || []
  const forecastRuns = metrics?.model_runs?.filter(r => r.task === 'forecasting') || []

  const chartData = forecastPoints.map(p => ({
    ts: new Date(p.target_timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    predicted: p.predicted_kwh != null ? +p.predicted_kwh.toFixed(4) : null,
    actual: p.actual_kwh != null ? +p.actual_kwh.toFixed(4) : null,
    model: p.model_name,
  }))

  const vsActualChart = vsActual.slice(-72).map(p => ({
    ts: new Date(p.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' }),
    predicted: p.predicted != null ? +p.predicted.toFixed(4) : null,
    actual: p.actual != null ? +p.actual.toFixed(4) : null,
  }))

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>📈 Energy Forecast</h1>
          <div className="section-sub">Hourly energy consumption predictions</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            Horizon:
            <select className="input" style={{ padding: '4px 8px', width: 90 }} value={hours}
              onChange={e => setHours(+e.target.value)}>
              {[12, 24, 48, 72, 168].map(h => <option key={h} value={h}>{h}h</option>)}
            </select>
          </label>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /></button>
        </div>
      </div>

      {/* Source badge */}
      {forecast && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className={`badge ${forecast.source === 'ml_model' ? 'badge-running' : 'badge-paused'}`}>
            {forecast.source === 'ml_model' ? '🤖 ML Model' : '📐 Naive Baseline'}
          </span>
          {forecast.source !== 'ml_model' && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 6, alignItems: 'center' }}>
              <Info size={12} /> No trained model — showing rolling mean baseline. Train a forecasting model to see real predictions.
            </span>
          )}
        </div>
      )}

      {loading
        ? <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
        : <>
            {/* Forecast chart */}
            <div className="card" style={{ marginBottom: 20 }}>
              <div className="section-title" style={{ marginBottom: 12 }}>
                {hours}h Forecast · Predicted Energy (kWh / hour)
              </div>
              {chartData.length === 0
                ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                    No forecast data — simulator needs data in DB first
                  </div>
                : <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <defs>
                        <linearGradient id="gpred" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="ts" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} interval="preserveStartEnd" />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kWh" />
                      <Tooltip {...CHART_TOOLTIP} />
                      <Area type="monotone" dataKey="predicted" name="Predicted kWh" stroke="#8b5cf6" fill="url(#gpred)" strokeWidth={2} dot={false} />
                      {chartData.some(p => p.actual != null) && (
                        <Line type="monotone" dataKey="actual" name="Actual kWh" stroke="#10b981" strokeWidth={1.5} dot={false} />
                      )}
                    </AreaChart>
                  </ResponsiveContainer>
              }
            </div>

            {/* Forecast vs Actual */}
            {vsActualChart.length > 0 && (
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="section-header">
                  <div className="section-title">Forecast vs Actual (last 72h)</div>
                  <div className="section-sub">How accurate were previous predictions?</div>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={vsActualChart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="ts" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} interval="preserveStartEnd" />
                    <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kWh" />
                    <Tooltip {...CHART_TOOLTIP} />
                    <Legend wrapperStyle={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }} />
                    <Line type="monotone" dataKey="predicted" name="Predicted" stroke="#8b5cf6" strokeWidth={1.5} dot={false} strokeDasharray="5 3" />
                    <Line type="monotone" dataKey="actual" name="Actual" stroke="#10b981" strokeWidth={1.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Model metrics table */}
            {forecastRuns.length > 0 && (
              <div className="card">
                <div className="section-title" style={{ marginBottom: 16 }}>Forecasting Model Runs</div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Model</th>
                        <th>MAE (kWh)</th>
                        <th>RMSE</th>
                        <th>R²</th>
                        <th>Train Rows</th>
                        <th>Trained At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecastRuns.map((r, i) => {
                        const m = typeof r.metrics === 'string' ? JSON.parse(r.metrics) : r.metrics || {}
                        return (
                          <tr key={i}>
                            <td className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem' }}>{r.model_name}</td>
                            <td className="mono">{m.mae != null ? m.mae.toFixed(4) : '—'}</td>
                            <td className="mono">{m.rmse != null ? m.rmse.toFixed(4) : '—'}</td>
                            <td className="mono">{m.r2 != null ? m.r2.toFixed(4) : '—'}</td>
                            <td className="mono">{(r.train_rows || 0).toLocaleString()}</td>
                            <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.trained_at?.slice(0, 19) || '—'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {forecastRuns.length === 0 && (
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-muted)' }}>
                <TrendingUp size={20} />
                <span style={{ fontSize: '0.85rem' }}>
                  No trained forecasting model found. Run{' '}
                  <code style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: 4 }}>python -m backend.app.ml.train_forecaster</code>
                  {' '}to train one.
                </span>
              </div>
            )}
          </>
      }
    </div>
  )
}
