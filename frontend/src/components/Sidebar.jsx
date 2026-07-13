export default function Sidebar({
  crops,
  selectedCrop,
  onCropChange,
  simEnabled,
  onToggleSim,
  overrides,
  onOverridesChange,
  currentInputs,
  currentCropPrice,
  onApplyOverrides,
  onResetOverrides,
}) {
  const handleFieldChange = (field) => (e) => {
    const value = e.target.value === '' ? '' : parseFloat(e.target.value)
    onOverridesChange({ ...overrides, [field]: value })
  }

  return (
    <aside className="sidebar">
      <img
        className="sidebar-logo"
        src="https://cdn-icons-png.flaticon.com/512/2909/2909564.png"
        alt="logo"
      />
      <h2>Kano GeoAI System</h2>
      <hr />

      <label className="field-label" htmlFor="crop-select">
        Select Crop to Analyze
      </label>
      <select
        id="crop-select"
        value={selectedCrop || ''}
        onChange={(e) => onCropChange(e.target.value)}
      >
        {crops.map((c) => (
          <option key={c.code} value={c.code}>
            {c.label}
          </option>
        ))}
      </select>

      <hr />
      <h3>🔮 Forecast Simulator</h3>
      <label className="checkbox-row">
        <input type="checkbox" checked={simEnabled} onChange={(e) => onToggleSim(e.target.checked)} />
        Enable Scenario Mode
      </label>

      {simEnabled && (
        <div className="sim-panel">
          <p className="hint">Adjust inputs to simulate scenarios.</p>

          <label className="field-label">Current price (₦)</label>
          <input
            type="number"
            step="500"
            value={overrides.crop_price ?? currentCropPrice ?? ''}
            onChange={handleFieldChange('crop_price')}
          />

          <label className="field-label">Exchange Rate (NGN/USD)</label>
          <input
            type="number"
            step="50"
            value={overrides.exchange_rate ?? currentInputs?.exchange_rate ?? ''}
            onChange={handleFieldChange('exchange_rate')}
          />

          <label className="field-label">NDVI Anomaly</label>
          <input
            type="number"
            step="0.1"
            value={overrides.ndvi_anomaly ?? currentInputs?.ndvi_anomaly ?? ''}
            onChange={handleFieldChange('ndvi_anomaly')}
          />

          <label className="field-label">NDMI Anomaly</label>
          <input
            type="number"
            step="0.1"
            value={overrides.ndmi_anomaly ?? currentInputs?.ndmi_anomaly ?? ''}
            onChange={handleFieldChange('ndmi_anomaly')}
          />

          <label className="field-label">Rainfall Anomaly</label>
          <input
            type="number"
            step="0.1"
            value={overrides.rainfall_anomaly ?? currentInputs?.rainfall_anomaly ?? ''}
            onChange={handleFieldChange('rainfall_anomaly')}
          />

          <div className="sim-buttons">
            <button className="btn-primary" onClick={onApplyOverrides}>
              Apply Scenario
            </button>
            <button className="btn-secondary" onClick={onResetOverrides}>
              Reset
            </button>
          </div>
        </div>
      )}
    </aside>
  )
}
