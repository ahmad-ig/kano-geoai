import { useEffect, useState, useCallback, useMemo } from 'react'
import Sidebar from './components/Sidebar.jsx'
import KpiCards from './components/KpiCards.jsx'
import PriceChart from './components/PriceChart.jsx'
import MapView from './components/MapView.jsx'
import { getCrops, getForecast, getHistorical, getMapData } from './api/client.js'

export default function App() {
  const [crops, setCrops] = useState([])
  const [selectedCrop, setSelectedCrop] = useState(null)

  const [simEnabled, setSimEnabled] = useState(false)
  const [overrides, setOverrides] = useState({}) // draft values, edited in the sidebar
  const [appliedOverrides, setAppliedOverrides] = useState({}) // values actually sent to /forecast

  const [forecast, setForecast] = useState(null)
  const [historical, setHistorical] = useState(null)
  const [mapData, setMapData] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Load crop list, historical data, and map data once on mount.
  useEffect(() => {
    async function loadStatic() {
      try {
        const [cropList, hist, map] = await Promise.all([
          getCrops(),
          getHistorical(24),
          getMapData(),
        ])
        setCrops(cropList)
        setSelectedCrop(cropList[0]?.code ?? null)
        setHistorical(hist)
        setMapData(map)
      } catch (e) {
        setError(formatError(e))
      }
    }
    loadStatic()
  }, [])

  // Fetch forecast whenever the selected crop or applied scenario overrides change.
  const fetchForecast = useCallback(async () => {
    if (!selectedCrop) return
    setLoading(true)
    setError(null)
    try {
      const params = { ...appliedOverrides }
      if (Object.keys(appliedOverrides).length > 0) {
        params.crop = selectedCrop // tell backend which crop's price override applies to
      }
      const data = await getForecast(params)
      setForecast(data)
    } catch (e) {
      setError(formatError(e))
    } finally {
      setLoading(false)
    }
  }, [selectedCrop, appliedOverrides])

  useEffect(() => {
    fetchForecast()
  }, [fetchForecast])

  const selectedCropForecast = useMemo(
    () => forecast?.prices.find((p) => p.crop === selectedCrop),
    [forecast, selectedCrop]
  )

  const handleApplyOverrides = () => setAppliedOverrides(overrides)
  const handleResetOverrides = () => {
    setOverrides({})
    setAppliedOverrides({})
  }

  return (
    <div className="app-shell">
      <Sidebar
        crops={crops}
        selectedCrop={selectedCrop}
        onCropChange={setSelectedCrop}
        simEnabled={simEnabled}
        onToggleSim={setSimEnabled}
        overrides={overrides}
        onOverridesChange={setOverrides}
        currentInputs={forecast?.current_inputs}
        currentCropPrice={selectedCropForecast?.current}
        onApplyOverrides={handleApplyOverrides}
        onResetOverrides={handleResetOverrides}
      />

      <main className="main-content">
        <h1>🌾 Kano State GeoAI Food Security Dashboard</h1>

        {error && <div className="error-banner">⚠️ {error}</div>}

        {forecast && (
          <p className="subtitle">
            <strong>Forecast Target:</strong> {formatMonthYear(forecast.forecast_date)} |{' '}
            <strong>Current Data:</strong> {formatMonthYear(forecast.current_date)}
          </p>
        )}
        <hr />

        {loading && !forecast ? (
          <p>Loading forecast…</p>
        ) : (
          <KpiCards forecast={forecast} selectedCropForecast={selectedCropForecast} simEnabled={simEnabled} />
        )}

        <hr />

        <div className="grid-row">
          <MapView mapData={mapData} />
          <PriceChart
            historicalRecords={historical?.records}
            selectedCrop={selectedCrop}
            selectedCropForecast={selectedCropForecast}
            forecastDate={forecast?.forecast_date}
          />
        </div>
      </main>
    </div>
  )
}

function formatMonthYear(isoDate) {
  if (!isoDate) return ''
  const d = new Date(isoDate)
  return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

function formatError(e) {
  return e?.response?.data?.detail || e?.message || 'Something went wrong.'
}
