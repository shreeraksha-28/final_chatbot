import axios from 'axios'

const BASE = ''  // Vite proxy forwards /chat and /recommend to :8000

export const startChat = () =>
  axios.post(`${BASE}/chat/start`).then(r => r.data)

export const sendStep = (session_id, step, answer) =>
  axios.post(`${BASE}/chat/step`, { session_id, step, answer }).then(r => r.data)

export const getRecommendations = (session_id) =>
  axios.post(`${BASE}/recommend`, { session_id }).then(r => r.data)
