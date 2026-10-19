import { useState, useEffect, useCallback } from 'react'
import { Sliders, Save, RefreshCw, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { getSettings, updateSetting } from '../api'

const SETTING_META = {
  tariff_inr_per_kwh: {
    label: 'Energy Tariff (INR / kWh)',
    description: 'Assumed flat-rate electricity tariff used for cost estimates. This is NOT your actual utility rate; it is a configurable assumption used in calculations.',
    unit: '₹/kWh',
    type: 'number',
    min: 0,
    step: 0.5,
  },
  anomaly_z_threshold: {
    label: 'Anomaly Z-Score Threshold',
    description: 'Z-score threshold for anomaly detection. Readings with |z| above this value are flagged. Lower = more sensitive.',
    unit: 'σ',
    type: 'number',
    min: 0.5,
    step: 0.1,
  },
  anomaly_abs_threshold_kw: {
    label: 'Anomaly Absolute Threshold (kW)',
    description: 'Readings with active power above this value are also flagged as anomalies regardless of z-score.',
    unit: 'kW',
    type: 'number',
    min: 0,
    step: 0.1,
  },
  anomaly_window_minutes: {
    label: 'Anomaly Rolling Window (minutes)',
    description: 'Rolling window size (in dataset minutes) used to compute mean and std for z-score anomaly detection.',
    unit: 'min',
    type: 'number',
    min: 10,
    step: 10,
  },
}

function SettingRow({ setting, onSave }) {
  const [val, setVal] = useState(setting.value)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [err, setErr] = useState(null)
  const meta = SETTING_META[setting.key] || {}
  const dirty = val !== setting.value

  const save = async () => {
    setSaving(true)
    setErr(null)
    try {
      await onSave(setting.key, val)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setErr('Save failed.')
    }
    setSaving(false)
  }

  return (
    <div style={{ borderBottom: '1px solid var(--border)', padding: '20px 0', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: 4 }}>
            {meta.label || setting.key}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', marginBottom: 6 }}>
            {setting.key}
          </div>
          {meta.description && (
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5, display: 'flex', gap: 8 }}>
              <Info size={12} style={{ flexShrink: 0, marginTop: 2, color: 'var(--accent-cyan)' }} />
              {meta.description}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div style={{ position: 'relative' }}>
            <input
              className="input"
              type={meta.type || 'text'}
              min={meta.min}
              step={meta.step}
              style={{ width: 140, textAlign: 'right', paddingRight: meta.unit ? '2.5rem' : undefined }}
              value={val}
              onChange={e => setVal(e.target.value)}
            />
            {meta.unit && (
              <span style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', fontSize: '0.72rem', color: 'var(--text-muted)', pointerEvents: 'none' }}>
                {meta.unit}
              </span>
            )}
          </div>
          <button
            className={`btn ${dirty ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '7px 14px' }}
            disabled={saving || !dirty}
            onClick={save}
          >
            {saving
              ? <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
              : saved
                ? <><CheckCircle size={13} /> Saved</>
                : <><Save size={13} /> Save</>
            }
          </button>
        </div>
      </div>
      {err && (
        <div style={{ fontSize: '0.75rem', color: 'var(--accent-red)', display: 'flex', gap: 6 }}>
          <AlertCircle size={12} /> {err}
        </div>
      )}
    </div>
  )
}

export default function Settings() {
  const [settings, setSettings] = useState([])
  const [loading, setLoading] = useState(true)
  const [globalSaved, setGlobalSaved] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const s = await getSettings()
      setSettings(s || [])
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleSave = useCallback(async (key, value) => {
    await updateSetting(key, value)
    setSettings(prev => prev.map(s => s.key === key ? { ...s, value: String(value) } : s))
    setGlobalSaved(true)
    setTimeout(() => setGlobalSaved(false), 2000)
  }, [])

  // Group: known vs unknown
  const knownKeys = Object.keys(SETTING_META)
  const known = settings.filter(s => knownKeys.includes(s.key))
  const other = settings.filter(s => !knownKeys.includes(s.key))

  return (
    <div className="animate-fade">
      <div className="section-header">
        <div>
          <h1 className="section-title" style={{ fontSize: '1.25rem' }}>⚙️ Settings</h1>
          <div className="section-sub">System configuration and threshold tuning</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {globalSaved && (
            <span style={{ fontSize: '0.78rem', color: 'var(--accent-green)', display: 'flex', gap: 6 }}>
              <CheckCircle size={13} /> Changes applied
            </span>
          )}
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> Reload</button>
        </div>
      </div>

      {/* Disclaimer */}
      <div style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, padding: '10px 16px', marginBottom: 24, fontSize: '0.78rem', color: 'var(--accent-yellow)', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
        <span>
          Changing anomaly thresholds will reload the anomaly detector in real-time.
          The tariff setting affects cost estimates only — it is a configurable assumption, not your actual utility rate.
        </span>
      </div>

      {loading
        ? <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
        : settings.length === 0
          ? <div className="card" style={{ display: 'flex', gap: 12, alignItems: 'center', color: 'var(--text-muted)' }}>
              <Sliders size={20} />
              <span style={{ fontSize: '0.85rem' }}>No settings found in database. Have you run the backend at least once?</span>
            </div>
          : <div className="card">
              {known.map(s => (
                <SettingRow key={s.key} setting={s} onSave={handleSave} />
              ))}
              {other.length > 0 && (
                <>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 20, marginBottom: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Other settings
                  </div>
                  {other.map(s => (
                    <SettingRow key={s.key} setting={s} onSave={handleSave} />
                  ))}
                </>
              )}
            </div>
      }
    </div>
  )
}
