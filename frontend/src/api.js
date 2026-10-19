import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE, timeout: 30000 })

export const simControl = (action, params = {}) =>
  api.post('/api/simulator/control', { action, ...params }).then(r => r.data)

export const getSimStatus = () =>
  api.get('/api/simulator/status').then(r => r.data)

export const getLatestReadings = (n = 60) =>
  api.get(`/api/readings/latest?n=${n}`).then(r => r.data)

export const getReadings = (params = {}) =>
  api.get('/api/readings/', { params }).then(r => r.data)

export const getReadingSummary = (params = {}) =>
  api.get('/api/readings/summary', { params }).then(r => r.data)

export const getHourlyAgg = (params = {}) =>
  api.get('/api/aggregates/hourly', { params }).then(r => r.data)

export const getDailyAgg = (params = {}) =>
  api.get('/api/aggregates/daily', { params }).then(r => r.data)

export const getHeatmap = () =>
  api.get('/api/aggregates/heatmap').then(r => r.data)

export const getComparison = (period = 'week') =>
  api.get(`/api/aggregates/comparison?period=${period}`).then(r => r.data)

export const getAlerts = (params = {}) =>
  api.get('/api/alerts/', { params }).then(r => r.data)

export const getAlertSummary = () =>
  api.get('/api/alerts/summary').then(r => r.data)

export const acknowledgeAlert = (id) =>
  api.post(`/api/alerts/${id}/acknowledge`).then(r => r.data)

export const getClassificationSummary = () =>
  api.get('/api/ml/classification/summary').then(r => r.data)

export const getForecast = (hours = 24) =>
  api.get(`/api/ml/forecast?hours_ahead=${hours}`).then(r => r.data)

export const getForecastVsActual = () =>
  api.get('/api/ml/forecast/vs-actual').then(r => r.data)

export const getModelMetrics = () =>
  api.get('/api/ml/metrics').then(r => r.data)

export const getRecommendations = () =>
  api.get('/api/recommendations/').then(r => r.data)

export const getSettings = () =>
  api.get('/api/settings/').then(r => r.data)

export const updateSetting = (key, value) =>
  api.put(`/api/settings/${key}`, { value: String(value) }).then(r => r.data)

// Blob-based CSV download (no popup blocker issues)
const downloadBlob = async (url, filename) => {
  const res = await api.get(url, { responseType: 'blob' })
  const href = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }))
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(href)
}

export const exportReadingsCSV = (params = {}) => {
  const qs = new URLSearchParams(params).toString()
  return downloadBlob(`/api/readings/export/csv?${qs}`, `energypulse_readings.csv`)
}

export const exportAlertsCSV = (params = {}) => {
  const qs = new URLSearchParams(params).toString()
  return downloadBlob(`/api/alerts/export/csv?${qs}`, `energypulse_alerts.csv`)
}

export default api
