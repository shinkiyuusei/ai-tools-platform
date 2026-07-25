import http from './http'

export const extensionApi = {
  /** List active extensions (public). */
  list() {
    return http.get('/extensions')
  },

  /** Get a single extension by id. */
  get(id) {
    return http.get(`/extensions/${id}`)
  },

  /** Admin: install extension. */
  install(id, manifest) {
    return http.post('/extensions/install', { id, manifest })
  },

  /** Admin: uninstall extension. */
  uninstall(id) {
    return http.delete(`/extensions/${id}`)
  },

  /** Admin: toggle status. */
  updateStatus(id, status) {
    return http.put(`/extensions/${id}/status`, { status })
  },

  /** Get current user's config for an extension. */
  getConfig(id) {
    return http.get(`/extensions/${id}/config`)
  },

  /** Update current user's config for an extension. */
  setConfig(id, config) {
    return http.put(`/extensions/${id}/config`, config)
  },

  /** Sandbox HTTP proxy. */
  proxyHttp(data) {
    return http.post('/extensions/proxy/http', data)
  },
}
