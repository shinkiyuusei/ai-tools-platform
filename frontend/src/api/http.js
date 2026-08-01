import axios from 'axios'
import { useToastStore } from '../stores/toast'

// 从 body data-api-prefix 读取 API 前缀（支持运行时配置）
const apiPrefix = document.body?.dataset?.apiPrefix || '/api/v1'

// NProgress 进度条工具
const NProgress = {
  _timer: null,
  _bar: null,
  _getBar() {
    if (!this._bar) {
      const el = document.getElementById('nprogress')
      this._bar = el ? el.querySelector('.bar') : null
    }
    return this._bar
  },
  start() {
    clearTimeout(this._timer)
    const bar = this._getBar()
    if (!bar) return
    bar.style.transition = 'none'
    bar.style.width = '0'
    bar.classList.remove('running')
    // force reflow
    bar.offsetHeight
    bar.style.transition = 'width 0.2s ease'
    bar.style.width = '30%'
  },
  done() {
    clearTimeout(this._timer)
    const bar = this._getBar()
    if (!bar) return
    bar.style.width = '100%'
    this._timer = setTimeout(() => {
      bar.classList.add('running')
      this._timer = setTimeout(() => {
        bar.style.width = '0'
        bar.classList.remove('running')
      }, 500)
    }, 150)
  },
  error() {
    clearTimeout(this._timer)
    const bar = this._getBar()
    if (!bar) return
    bar.style.background = 'linear-gradient(90deg, #c85554, #e08080, #c85554)'
    bar.style.boxShadow = '0 0 10px rgba(200, 85, 84, 0.5)'
    bar.style.width = '100%'
    this._timer = setTimeout(() => {
      bar.style.width = '0'
      bar.style.background = 'linear-gradient(90deg, #7b9cbf, #a3bedb, #7b9cbf)'
      bar.style.boxShadow = '0 0 10px rgba(123, 156, 191, 0.5)'
    }, 2000)
  },
}

// Toast: render directly via the Pinia toast store.
function showToast(message, type) {
  useToastStore().show(message, type)
}

let activeRequests = 0

const http = axios.create({
  baseURL: apiPrefix,
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

    // NProgress: 请求计数
    activeRequests++
    NProgress.start()

    return config
  },
  (error) => {
    activeRequests--
    if (activeRequests <= 0) {
      activeRequests = 0
      NProgress.error()
    }
    return Promise.reject(error)
  },
)

http.interceptors.response.use(
  (response) => {
    activeRequests--
    if (activeRequests <= 0) {
      activeRequests = 0
      NProgress.done()
    }

    const { data } = response
    if (data.code !== 0) {
      showToast(data.message || '请求失败', 'error')
      return Promise.reject(data)
    }
    return data
  },
  async (error) => {
    activeRequests--
    if (activeRequests <= 0) {
      activeRequests = 0
      NProgress.error()
    }

    const originalRequest = error.config
    const status = error.response?.status

    if (status === 401 && !originalRequest._retry) {
      if (!isRefreshing) {
        isRefreshing = true
        originalRequest._retry = true

        try {
          await axios.post(`${apiPrefix}/user/refresh`, {}, { withCredentials: true })
          resolvePendingRequests()
          return http(originalRequest)
        } catch {
          rejectPendingRequests()
          // Clear auth state
          try {
            await axios.post(`${apiPrefix}/user/logout`, {}, { withCredentials: true })
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
    showToast(message, 'error')
    return Promise.reject(error)
  },
)

export default http
