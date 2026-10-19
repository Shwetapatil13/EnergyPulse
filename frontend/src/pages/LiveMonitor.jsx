import { useState, useEffect, useRef, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Play, Pause, Square, SkipForward, Zap, DollarSign, Activity, Thermometer } from 'lucide-react'
import { simControl, getSimStatus } from '../api'

const MAX_POINTS = 120

function StatCard({ label, value, unit, color = '#3b82f6', icon: Icon, sublabel }) {
  return (
    <div className="stat-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value" style={{ color }}>
            {value ?? <span style={{ opacity: 0.3 }}>—</span>}
            {value != null && <span className="stat-unit" style={{ fontSize: '1rem', marginLeft: 4 }}>{unit}</span>}
          </div>
          {sublabel && <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 4 }}>{sublabel}</div>}
        </div>
        {Icon && <Icon size={24} style={{ color, opacity: 0.6 }} />}
      </div>
    </div>
  )
}

export default function LiveMonitor({ lastMessage, connected }) {
  const [chartData, setChartData] = useState([])
  const [simStatus, setSimStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [seekDate, setSeekDate] = useState('2007-06-01')
  const [speed, setSpeed] = useState(5)
  const cumulativeKwh = useRef(0)
  const prevTs = useRef(null)

  // Poll sim status
  useEffect(() => {
    const fetch = () => getSimStatus().then(setSimStatus).catch(() => {})
    fetch()
    const id = setInterval(fetch, 3000)
    return () => clearInterval(id)
  }, [])

  // Process incoming WS messages
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'reading') return
    const { timestamp, active_power_kw, energy_kwh, cost_inr, voltage_v, current_a, class_label, is_anomaly } = lastMessage

    if (energy_kwh != null) {
      cumulativeKwh.current += energy_kwh
    }

    const point = {
      t: new Date(timestamp).toLocaleTimeString(),
      ts: timestamp,
      kw: active_power_kw != null ? +active_power_kw.toFixed(4) : null,
      kwh: energy_kwh != null ? +energy_kwh.toFixed(6) : null,
      voltage: voltage_v != null ? +voltage_v.toFixed(2) : null,
      current: current_a != null ? +current_a.toFixed(3) : null,
      cost: cost_inr != null ? +cost_inr.toFixed(6) : null,
      class: class_label,
      anomaly: is_anomaly,
    }

    setChartData(prev => {
      const next = [...prev, point]
      return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next
    })
  }, [lastMessage])

  const handleControl = async (action, extra = {}) => {
    setLoading(true)
    try { await simControl(action, extra) }
    catch (e) { console.error(e) }
    finally {
      setLoading(false)
      setTimeout(() => getSimStatus().then(setSimStatus).catch(() => {}), 500)
    }
  }

  const latest = lastMessage?.type === 'reading' ? lastMessage : null
  const state = simStatus?.state || 'stopped'
  const progress = simStatus?.progress_pct || 0

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>⚡ Live Monitor</h1>
          <div className="section-sub">Real-time dataset replay · {simStatus?.current_timestamp?.split('T')[0] || '—'}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {connected && state === 'running' && <><div className="live-dot" /><span style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>LIVE</span></>}
          <span className={`badge badge-${state}`}>{state.toUpperCase()}</span>
        </div>
      </div>

      {/* Playback controls */}
      <div className="playback-bar" style={{ marginBottom: 20 }}>
        <button id="btn-start" className="btn btn-success" disabled={loading || state === 'running'}
          onClick={() => handleControl('start', { speed, start_date: seekDate || undefined, loop: true })}>
          <Play size={14} /> Start
        </button>
        <button id="btn-pause" className="btn btn-ghost" disabled={loading || state !== 'running'}
          onClick={() => handleControl('pause')}>
          <Pause size={14} /> Pause
        </button>
        <button id="btn-resume" className="btn btn-ghost" disabled={loading || state !== 'paused'}
          onClick={() => handleControl('resume')}>
          <Play size={14} /> Resume
        </button>
        <button id="btn-stop" className="btn btn-danger" disabled={loading || state === 'stopped'}
          onClick={() => handleControl('stop')}>
          <Square size={14} /> Stop
        </button>

        <div style={{ width: 1, background: 'var(--border)', height: 28, margin: '0 4px' }} />

        <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
          Speed:
          <select className="input" style={{ padding: '4px 8px', width: 90 }} value={speed}
            onChange={e => { const s = +e.target.value; setSpeed(s); if (state === 'running') handleControl('set_speed', { speed: s }) }}>
            {[0.5,1,2,5,10,30,60].map(v => <option key={v} value={v}>{v}×</option>)}
          </select>
        </label>

        <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
          From:
          <input className="input" type="date" style={{ padding: '4px 8px' }}
            min="2006-12-16" max="2010-11-26"
            value={seekDate} onChange={e => setSeekDate(e.target.value)} />
        </label>

        {state !== 'stopped' && (
          <button className="btn btn-ghost" disabled={loading}
            onClick={() => handleControl('seek', { start_date: seekDate })}>
            <SkipForward size={14} /> Seek
          </button>
        )}

        {/* Progress */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, marginLeft: 8 }}>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            {progress.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard label="Active Power" icon={Activity}
          value={latest?.active_power_kw?.toFixed(3)} unit="kW"
          color="#3b82f6"
          sublabel={<span className={`badge badge-${latest?.class_label || 'stopped'}`}>{latest?.class_label || '—'}</span>} />
        <StatCard label="Cumulative Energy" icon={Zap}
          value={cumulativeKwh.current.toFixed(4)} unit="kWh"
          color="#06b6d4" sublabel="Session total" />
        <StatCard label="Voltage" icon={Thermometer}
          value={latest?.voltage_v?.toFixed(1)} unit="V"
          color="#8b5cf6" sublabel={`Current: ${latest?.current_a?.toFixed(2) ?? '—'} A`} />
        <StatCard label="Est. Cost (session)" icon={DollarSign}
          value={`₹${(cumulativeKwh.current * 8).toFixed(2)}`} unit=""
          color="#10b981" sublabel="INR 8/kWh (assumed flat rate)" />
      </div>

      {/* Live chart */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-header">
          <div>
            <div className="section-title">Active Power (kW) — Last {MAX_POINTS} readings</div>
            <div className="section-sub">1 reading ≈ 1 minute of dataset time · anomalies shown in red</div>
          </div>
        </div>
        {chartData.length === 0
          ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              {state === 'stopped' ? 'Press Start to begin simulation' : 'Waiting for data...'}
            </div>
          : <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="t" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} unit=" kW" />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8 }}
                  labelStyle={{ color: 'var(--text-secondary)', fontSize: 11 }}
                  formatter={(v, n) => [v?.toFixed(4), n]}
                />
                <Line dataKey="kw" name="Active Power (kW)" stroke="#3b82f6" strokeWidth={1.5} dot={false}
                  activeDot={{ r: 4, fill: '#3b82f6' }} />
              </LineChart>
            </ResponsiveContainer>
        }
      </div>

      {/* Latest reading raw */}
      {latest && (
        <div className="card">
          <div className="section-title" style={{ marginBottom: 12 }}>Latest Reading</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
            {[
              ['Timestamp', latest.timestamp?.replace('T',' ').slice(0,19)],
              ['Active Power', `${latest.active_power_kw?.toFixed(4)} kW`],
              ['Reactive Power', `${latest.reactive_power_kw?.toFixed(4)} kW`],
              ['Voltage', `${latest.voltage_v?.toFixed(2)} V`],
              ['Current', `${latest.current_a?.toFixed(3)} A`],
              ['Energy/min', `${latest.energy_kwh?.toFixed(6)} kWh`],
              ['Cost/min', `₹${latest.cost_inr?.toFixed(6)}`],
              ['Zone 1', `${latest.sub_metering_1_wh?.toFixed(1)} Wh`],
              ['Zone 2', `${latest.sub_metering_2_wh?.toFixed(1)} Wh`],
              ['Zone 3', `${latest.sub_metering_3_wh?.toFixed(1)} Wh`],
              ['Class', latest.class_label],
              ['Anomaly', latest.is_anomaly ? '⚠ YES' : 'No'],
            ].map(([k, v]) => (
              <div key={k} style={{ background: 'var(--bg-secondary)', borderRadius: 6, padding: '8px 12px' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>{k}</div>
                <div className="mono" style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{v ?? '—'}</div>
              </div>
            ))}
          </div>
          {latest.is_anomaly && latest.alerts?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              {latest.alerts.map((a, i) => (
                <div key={i} className={`alert-item alert-${a.severity}`}>
                  <span style={{ fontSize: '0.8rem' }}>⚠</span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.82rem' }}>{a.type.replace(/_/g,' ').toUpperCase()} — {a.severity}</div>
                    <div style={{ fontSize: '0.77rem', color: 'var(--text-secondary)', marginTop: 2 }}>{a.description}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
