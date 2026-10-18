import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';

export default function App() {
  const [selectedCrop, setSelectedCrop] = useState("Maize");

  // Simulation state
  const [enableSim, setEnableSim] = useState(false);
  const [simPrice, setSimPrice] = useState(40000); // Default simulated price
  const [ndviAnomaly, setNdviAnomaly] = useState(0.0);
  const [ndmiAnomaly, setNdmiAnomaly] = useState(0.0);
  const [rainfallAnomaly, setRainfallAnomaly] = useState(0.0);

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch data from FastAPI
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Build the URL with all simulation parameters if simulation is enabled
        let url = `http://127.0.0.1:8000/api/dashboard?crop=${selectedCrop}&sim=${enableSim}`;
        if (enableSim) {
          url += `&current_price=${simPrice}&ndvi_anomaly=${ndviAnomaly}&ndmi_anomaly=${ndmiAnomaly}&rainfall_anomaly=${rainfallAnomaly}`;
        }

        const response = await fetch(url);
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
      setLoading(false);
    };

    // Adding a slight ounce so it doesn't crash the server while sliding
    const timeoutId = setTimeout(() => fetchData(), 300); // 300ms delay
    return () => clearTimeout(timeoutId); // Cleanup on unmount or before next fetch

  }, [selectedCrop, enableSim, simPrice, ndviAnomaly, ndmiAnomaly, rainfallAnomaly]);

  if (loading && !dashboardData) {
    return <div className="flex justify-center items-center h-screen text-xl font-bold">🔄 Loading Kano GeoAI Data...</div>;
  }

  const { stress_val, price_preds, kano_geojson, map_data, history_data } = dashboardData || {};
  const isHighRisk = stress_val < -1.0;
  const cropName = selectedCrop.replace('Price_', '');
  
  return (
    <div className="flex min-h-screen bg-gray-100 font-sans">
      
      {/* SIDEBAR */}
      <div className="w-80 bg-white shadow-lg p-6 flex flex-col border-r border-gray-200">
        <h2 className="text-xl font-bold mb-6">Kano GeoAI System</h2>
        
        <label className="font-bold text-gray-700 mb-2">Select Crop to Analyze</label>
        <select 
          className="p-2 border rounded mb-8 bg-gray-50"
          value={selectedCrop}
          onChange={(e) => setSelectedCrop(e.target.value)}
        >
          <option value="Maize">Maize</option>
          <option value="Rice">Rice</option>
          <option value="Millet">Millet</option>
          <option value="Sorghum">Sorghum</option>
        </select>

        <div className="border-t pt-6">
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2">🔮 Forecast Simulator</h3>
          
          <label className="flex items-center gap-2 cursor-pointer mb-6">
            <input 
              type="checkbox" 
              checked={enableSim} 
              onChange={(e) => setEnableSim(e.target.checked)}
              className="w-5 h-5 text-blue-600"
            />
            <span className="font-semibold text-gray-700">Enable Scenario Mode</span>
          </label>

          {enableSim && (
            <div className="space-y-4 bg-blue-50 p-4 rounded border border-blue-100">
              <div>
                <label className="block text-sm font-semibold mb-1">Simulate {cropName} Price (₦)</label>
                <input type="number" value={simPrice} onChange={(e) => setSimPrice(e.target.value)} className="w-full p-2 border rounded" step="500" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">NDVI Anomaly ({ndviAnomaly})</label>
                <input type="range" min="-3" max="3" step="0.1" value={ndviAnomaly} onChange={(e) => setNdviAnomaly(e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">NDMI Anomaly ({ndmiAnomaly})</label>
                <input type="range" min="-3" max="3" step="0.1" value={ndmiAnomaly} onChange={(e) => setNdmiAnomaly(e.target.value)} className="w-full" />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Rainfall Anomaly ({rainfallAnomaly})</label>
                <input type="range" min="-3" max="3" step="0.1" value={rainfallAnomaly} onChange={(e) => setRainfallAnomaly(e.target.value)} className="w-full" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* MAIN DASHBOARD */}
      <div className="flex-1 p-8 overflow-y-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">🌾 Kano State GeoAI Food Security Dashboard</h1>
        </header>

        {dashboardData && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className={`p-6 rounded-lg border-l-4 ${isHighRisk ? 'bg-red-50 border-red-600' : 'bg-white border-green-600 shadow-md'}`}>
                <h3 className={`text-lg font-bold ${isHighRisk ? 'text-red-600' : 'text-green-700'}`}>
                  {isHighRisk ? '🔴 HIGH DROUGHT RISK' : '🟢 NORMAL CONDITIONS'}
                </h3>
                <p className="text-2xl mt-2 font-semibold">Index: {stress_val !== null ? stress_val.toFixed(3) : 'N/A'}</p>
              </div>

              <div className="p-6 rounded-lg bg-white shadow-md border-l-4 border-blue-600">
                <h3 className="text-lg font-bold text-gray-700">💰 {cropName} Price Forecast</h3>
                <p className="text-3xl mt-2 font-bold">₦{price_preds.pred?.toLocaleString()}</p>
                <p className={`text-md font-semibold mt-1 ${price_preds.change > 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {price_preds.change > 0 ? '▲' : '▼'} ₦{Math.abs(price_preds.change)?.toLocaleString()} change
                </p>
              </div>

              <div className="p-6 rounded-lg bg-white shadow-md border-l-4 border-purple-600">
                <h3 className="text-lg font-bold text-gray-700">📊 Market Trend</h3>
                <p className="text-2xl mt-2 font-semibold">{price_preds.change > 0 ? 'Inflationary' : 'Deflationary'}</p>
                <p className="text-sm text-gray-500 mt-1">Current: ₦{price_preds.current?.toLocaleString()}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-4 rounded-lg shadow-md">
                <h3 className="text-xl font-bold mb-4">🗺️ Live Crop Health Heatmap</h3>
                <Plot
                  data={[{
                    type: 'choropleth',
                    locations: map_data?.lga_names,
                    z: map_data?.ndvi_values,
                    geojson: kano_geojson,
                    featureidkey: 'properties.lga_name',
                    colorscale: 'RdYlGn',
                    marker: { line: { width: 1, color: 'white' } }
                  }]}
                  layout={{
                    geo: { fitbounds: "locations", visible: false },
                    margin: { r: 0, t: 0, l: 0, b: 0 },
                    height: 450
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '450px' }}
                />
              </div>

              <div className="bg-white p-4 rounded-lg shadow-md">
                <h3 className="text-xl font-bold mb-4">📈 24-Month Trajectory: {cropName}</h3>
                <Plot
                  data={[
                    {
                      x: history_data?.dates, 
                      y: history_data?.prices, 
                      type: 'scatter', 
                      mode: 'lines+markers', 
                      name: 'History',
                      line: { color: '#1f77b4', width: 3 }
                    },
                    {
                      x: [history_data?.dates?.[history_data.dates.length - 1], "2025-01-01"], 
                      y: [history_data?.prices?.[history_data.prices.length - 1], price_preds.pred],
                      type: 'scatter',
                      mode: 'lines+markers',
                      name: 'Forecast',
                      line: { color: '#d62728', width: 3, dash: 'dot' },
                      marker: { size: 10, symbol: 'star' }
                    }
                  ]}
                  layout={{
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Price (NGN)' },
                    margin: { t: 10 },
                    height: 450
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '450px' }}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}