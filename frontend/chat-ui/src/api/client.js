import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 120_000,  // LLM can be slow on first run
})

/**
 * Send a chat message to the agent backend.
 * @param {string} session - Unique session ID
 * @param {string} message - User message text
 * @returns {Promise<string>} - Assistant reply
 */
export async function sendMessage(session, message) {
  const { data } = await api.post('/api/chat', { session, message })
  return data.response
}

/**
 * Fetch conversation history for a session.
 */
export async function getHistory(session) {
  const { data } = await api.get(`/api/chat/history/${session}`)
  return data.history
}

/**
 * Clear conversation history for a session.
 */
export async function clearHistory(session) {
  await api.delete(`/api/chat/history/${session}`)
}

/**
 * Get the user profile stored in MongoDB.
 */
export async function getUserProfile(session) {
  const { data } = await api.get(`/api/profile/${session}`)
  return data
}
