import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=UTF-8',
  },
})

http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
  (error) => {
    const message = error.response?.data?.message || error.message || '网络异常，请稍后重试'
    window.dispatchEvent(new CustomEvent('app:error', { detail: message }))
    return Promise.reject(error)
  },
)

export default http
