import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
  },
})

let isRefreshing = false
let pendingRequests = []

function resolvePendingRequests() {
  pendingRequests.forEach((cb) => cb())
  pendingRequests = []
}

function rejectPendingRequests() {
  pendingRequests.forEach((cb) => cb(null))
  pendingRequests = []
}

http.interceptors.request.use(
  (config) => {
    // Attach CSRF token from non-httpOnly cookie (set by Flask-JWT-Extended)
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_access_token='))
      ?.split('=')[1]
    if (csrfToken) {
      config.headers['X-CSRF-TOKEN'] = csrfToken
    }

    if (config.method === 'get') {
      const params = config.params || {}
      config.params = {
        pageNum: 1,
        pageSize: 10,
        ...params,
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

http.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code !== 0) {
      window.dispatchEvent(
        new CustomEvent('app:error', {
          detail: data.message || '请求失败',
        }),
      )
      return Promise.reject(data)
    }
    return data
  },
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    if (status === 401 && !originalRequest._retry) {
      if (!isRefreshing) {
        isRefreshing = true
        originalRequest._retry = true

        try {
          await axios.post('/api/v1/user/refresh', {}, { withCredentials: true })
          resolvePendingRequests()
          return http(originalRequest)
        } catch {
          rejectPendingRequests()
          // Clear auth state
          try {
            await axios.post('/api/v1/user/logout', {}, { withCredentials: true })
          } catch {
            // ignore
          }
          window.dispatchEvent(new CustomEvent('app:auth-expired'))
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      } else {
        return new Promise((resolve) => {
          pendingRequests.push(() => {
            resolve(http(originalRequest))
          })
        })
      }
    }

    const message = error.response?.data?.message || error.message || '网络异常，请稍后重试'
    window.dispatchEvent(new CustomEvent('app:error', { detail: message }))
    return Promise.reject(error)
  },
)

export default http
