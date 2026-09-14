import http from './http'

export const extensionApi = {
  /** List active extensions (public). */
  list() {
    return http.get('/extensions')
  },

  /** Get current user's config for an extension. */
  getConfig(id) {
    return http.get(`/extensions/${id}/config`)
  },

  /** Sandbox HTTP proxy. */
  proxyHttp(data) {
    return http.post('/extensions/proxy/http', data)
  },
}
