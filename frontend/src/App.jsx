import { useState, useEffect, useCallback, useRef } from 'react'
import LiveMonitor from './pages/LiveMonitor'
import Historical from './pages/Historical'
import Classification from './pages/Classification'
import Forecast from './pages/Forecast'
import Alerts from './pages/Alerts'
import Recommendations from './pages/Recommendations'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import { useWebSocket } from './hooks/useWebSocket'
import { Activity, BarChart2, Brain, TrendingUp, Bell, Lightbulb, FileText, Sliders, Zap, Wifi, WifiOff } from 'lucide-react'

const TABS = [
  { id: 'live',            label: 'Live Monitor',      icon: Activity },
  { id: 'historical',     label: 'Historical',        icon: BarChart2 },
  { id: 'classification', label: 'Classification',    icon: Brain },
  { id: 'forecast',       label: 'Forecast',          icon: TrendingUp },
  { id: 'alerts',         label: 'Alerts',            icon: Bell },
  { id: 'recommendations',label: 'Recommendations',   icon: Lightbulb },
  { id: 'reports',        label: 'Reports',           icon: FileText },
  { id: 'settings',       label: 'Settings',          icon: Sliders },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('live')
  const [alertCount, setAlertCount] = useState(0)
  const { lastMessage, connected, reconnect } = useWebSocket(
    import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live'
  )

  // Track alert count from WS
  useEffect(() => {
    if (lastMessage?.alerts?.length) {
      setAlertCount(c => c + lastMessage.alerts.length)
    }
  }, [lastMessage])

  const connStatus = connected ? 'connected' : 'disconnected'

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">⚡</div>
          <div>
            <div className="logo-text">EnergyPulse</div>
            <div className="logo-sub">Smart Energy Monitor</div>
          </div>
        </div>

        <nav style={{ flex: 1, overflowY: 'auto', padding: '8px 0', marginTop: '4px' }}>
          {TABS.map(tab => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <div
                key={tab.id}
                id={`nav-${tab.id}`}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id)
                  if (tab.id === 'alerts') setAlertCount(0)
                }}
              >
                <Icon size={16} />
                {tab.label}
                {tab.id === 'alerts' && alertCount > 0 && (
                  <span className="nav-badge">{alertCount > 99 ? '99+' : alertCount}</span>
                )}
              </div>
            )
          })}
        </nav>

        {/* Bottom: connection status */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
          <div className={`conn-status`} style={{ color: 'var(--text-muted)', gap: '8px' }}>
            <div className={`conn-dot ${connStatus}`} />
            <span style={{ fontSize: '0.72rem' }}>
              WS {connected ? 'Connected' : 'Disconnected'}
            </span>
            {!connected && (
              <button className="btn btn-ghost" style={{ padding: '2px 8px', fontSize: '0.7rem', marginLeft: 'auto' }} onClick={reconnect}>
                Retry
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <span className="sim-banner" style={{ flex: 1 }}>
            <span>🔬</span>
            <span><strong>Dataset-based simulation</strong> — not physical sensor measurements | UCI Household Power Consumption (2006–2010)</span>
          </span>
          <div className="badge badge-sim" style={{ flexShrink: 0 }}>
            <span>SIMULATED DATA</span>
          </div>
        </header>

        {/* Page */}
        <main className="page-content animate-fade" key={activeTab}>
          {activeTab === 'live'            && <LiveMonitor lastMessage={lastMessage} connected={connected} />}
          {activeTab === 'historical'     && <Historical />}
          {activeTab === 'classification' && <Classification />}
          {activeTab === 'forecast'       && <Forecast />}
          {activeTab === 'alerts'         && <Alerts />}
          {activeTab === 'recommendations'&& <Recommendations />}
          {activeTab === 'reports'        && <Reports />}
          {activeTab === 'settings'       && <Settings />}
        </main>
      </div>
    </div>
  )
}
