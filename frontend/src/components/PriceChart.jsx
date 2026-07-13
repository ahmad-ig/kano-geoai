import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

export default function PriceChart({ historicalRecords, selectedCrop, selectedCropForecast, forecastDate }) {
  if (!historicalRecords?.length || !selectedCropForecast) return null

  const history = historicalRecords
    .filter((r) => r[selectedCrop] != null)
    .map((r) => ({ date: r.Date, history: r[selectedCrop], forecast: null }))

  const lastHistoryPoint = history[history.length - 1]

  const forecastSegment = [
    { date: lastHistoryPoint.date, history: null, forecast: lastHistoryPoint.history },
    { date: forecastDate, history: null, forecast: selectedCropForecast.predicted },
  ]

  const chartData = [...history, ...forecastSegment]

  return (
    <div className="chart-card">
      <h3>📈 {history.length}-Month Trajectory: {selectedCropForecast.label}</h3>
      <p className="hint">Historical trends vs AI Prediction</p>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={20} />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) => `₦${(v / 1000).toFixed(0)}k`}
            width={60}
          />
          <Tooltip
            formatter={(value) => (value == null ? '—' : `₦${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`)}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="history"
            name="History"
            stroke="#1f77b4"
            strokeWidth={3}
            dot={{ r: 2 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="#d62728"
            strokeWidth={3}
            strokeDasharray="6 4"
            dot={{ r: 5 }}
            connectNulls={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
