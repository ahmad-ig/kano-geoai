import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const client = axios.create({ baseURL, timeout: 20000 })

export const getCrops = () => client.get('/crops').then((r) => r.data)

export const getForecast = (overrides = {}) =>
  client.get('/forecast', { params: overrides }).then((r) => r.data)

export const getHistorical = (months = 24) =>
  client.get('/historical', { params: { months } }).then((r) => r.data)

export const getMapData = () => client.get('/map-data').then((r) => r.data)

export default client
