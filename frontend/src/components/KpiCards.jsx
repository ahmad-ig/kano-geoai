const STATUS_ICON = {
  green: '🟢',
  orange: '🟡',
  red: '🔴',
  gray: '⚪',
}

export default function KpiCards({ forecast, selectedCropForecast, simEnabled }) {
  if (!forecast || !selectedCropForecast) return null

  const { stress } = forecast
  const change = selectedCropForecast.change
  const isUp = change > 0

  return (
    <div className="kpi-row">
      <div className={`kpi-card ${stress.severity === 'red' ? 'warning-card' : 'metric-card'}`}>
        <h3>🌱 Forecasted Vegetation</h3>
        <p className="kpi-status" style={{ color: stress.severity }}>
          {STATUS_ICON[stress.severity]} {stress.status}
        </p>
        <p className="kpi-value">Index: {stress.value.toFixed(3)}</p>
      </div>

      <div className="kpi-card metric-card">
        <h3>💰 {selectedCropForecast.label} Price Forecast</h3>
        <p className="kpi-value">₦{selectedCropForecast.predicted.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
        <p className={isUp ? 'delta-up' : 'delta-down'}>
          {isUp ? '▲' : '▼'} {change >= 0 ? '+' : ''}
          {change.toLocaleString(undefined, { maximumFractionDigits: 0 })} ({selectedCropForecast.change_pct.toFixed(1)}%)
        </p>
      </div>

      <div className="kpi-card metric-card">
        <h3>📊 Market Trend</h3>
        <p className="kpi-value">{isUp ? 'Inflationary' : 'Deflationary'} Trend</p>
        <p>Current: ₦{selectedCropForecast.current.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
        {simEnabled && <small>Simulated Input Active</small>}
      </div>
    </div>
  )
}
