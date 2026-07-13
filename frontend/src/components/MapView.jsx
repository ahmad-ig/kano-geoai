import Plot from 'react-plotly.js'

export default function MapView({ mapData }) {
  if (!mapData || !mapData.lga_data?.length) {
    return (
      <div className="chart-card">
        <h3>🗺️ Live Crop Health Heatmap</h3>
        <p className="hint">⚠️ No map data available for the current month.</p>
      </div>
    )
  }

  const { geojson, lga_data: lgaData } = mapData
  const ndviValues = lgaData.map((d) => d.ndvi)

  return (
    <div className="chart-card">
      <h3>🗺️ Live Crop Health Heatmap</h3>
      <p className="hint">Vegetation Health (NDVI) across Kano State LGAs</p>
      <Plot
        data={[
          {
            type: 'choroplethmapbox',
            geojson,
            locations: lgaData.map((d) => d.lga_name),
            z: ndviValues,
            zmin: Math.min(...ndviValues),
            zmax: Math.max(...ndviValues),
            colorscale: 'RdYlGn',
            featureidkey: 'properties.lga_name',
            marker: { line: { width: 1, color: 'white' }, opacity: 0.8 },
            hovertemplate:
              '<b>%{location}</b><br>NDVI: %{z}<extra></extra>',
            customdata: lgaData.map((d) => d.rainfall),
            colorbar: { title: 'NDVI' },
          },
        ]}
        layout={{
          mapbox: {
            style: 'carto-positron',
            zoom: 7.2,
            center: { lat: 11.7, lon: 8.5 },
          },
          margin: { r: 0, t: 0, l: 0, b: 0 },
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          height: 400,
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '400px' }}
      />
    </div>
  )
}
