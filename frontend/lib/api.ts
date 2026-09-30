/**
 * API client — typed wrapper around axios for the Privacy Eye backend.
 */
import axios, { AxiosError } from 'axios'
import Cookies from 'js-cookie'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min for video uploads
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    if (err.response?.status === 401) {
      const refresh = Cookies.get('refresh_token')
      if (refresh) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, null, {
            params: { refresh_token: refresh },
          })
          const { access_token } = res.data
          Cookies.set('access_token', access_token, { secure: true, sameSite: 'strict' })
          if (err.config) {
            err.config.headers.Authorization = `Bearer ${access_token}`
            return api.request(err.config)
          }
        } catch {
          Cookies.remove('access_token')
          Cookies.remove('refresh_token')
          window.location.href = '/auth/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post('/auth/register', { email, password, full_name }),

  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, refresh_token } = res.data
    Cookies.set('access_token',  access_token,  { secure: true, sameSite: 'strict', expires: 1 })
    Cookies.set('refresh_token', refresh_token, { secure: true, sameSite: 'strict', expires: 7 })
    return res.data
  },

  me: () => api.get('/auth/me'),

  logout: () => {
    Cookies.remove('access_token')
    Cookies.remove('refresh_token')
  },
}

// ── Analysis ──────────────────────────────────────────────────────────────────
export const analysisApi = {
  analyzeImage: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => e, // can be used for progress bar
    })
  },

  analyzeVideo: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/video', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  analyzeAudio: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/audio', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getHistory: (page = 1, perPage = 10, mediaType?: string) =>
    api.get('/analyze/history', { params: { page, per_page: perPage, media_type: mediaType } }),

  getAnalysis: (id: string) => api.get(`/analyze/${id}`),

  deleteAnalysis: (id: string) => api.delete(`/analyze/${id}`),

  getStats: () => api.get('/analyze/stats'),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  generate: (analysisId: string) => api.post(`/reports/${analysisId}/generate`),
  get:      (analysisId: string) => api.get(`/reports/${analysisId}`),
  downloadJson: (analysisId: string) =>
    api.get(`/reports/${analysisId}/download/json`, { responseType: 'blob' }),
}

// ── Live Camera Scan ─────────────────────────────────────────────────────────
export const liveScanApi = {
  analyzeFrame: (payload: { session_id: string; image_base64: string; run_challenge?: boolean }) =>
    api.post('/live/frame', payload),

  requestChallenge: (sessionId: string) =>
    api.post('/live/challenge', null, { params: { session_id: sessionId } }),

  saveAudit: (payload: {
    session_id: string
    assessment: string
    category_label?: string
    confidence: number
    quality_index: number
    signals: any[]
    explanation: string
    snapshot_base64?: string
    consent_given?: boolean
    landmarks?: any
    eye_status?: string
    blink_count?: number
    phone_detected?: boolean
    presentation_attack?: boolean
    reason_codes?: string[]
  }) => api.post('/live/save-audit', payload),

  submitConsent: (payload: {
    session_id: string
    consent_given: boolean
    category_label: string
    confidence: number
    quality_score?: number
    face_snapshot_base64?: string
    landmarks?: any
  }) => api.post('/live/consent-response', payload),

  getTrainingStats: () => api.get('/live/training-stats'),
}

// ── Helpers ───────────────────────────────────────────────────────────────────
export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) return data.detail.map((d: { msg: string }) => d.msg).join(', ')
    return err.message
  }
  return 'An unexpected error occurred.'
}
