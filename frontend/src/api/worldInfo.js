import http from './http'

export const worldInfoApi = {
  /** List all entries for an entity. */
  list(entityType, entityId) {
    return http.get('/world-info/entries', { params: { entityType, entityId } })
  },

  /** Get a single entry by id. */
  get(id) {
    return http.get(`/world-info/entry/${id}`)
  },

  /** Create a new entry. */
  create(data) {
    return http.post('/world-info/entry', data)
  },

  /** Update an existing entry. */
  update(id, data) {
    return http.put(`/world-info/entry/${id}`, data)
  },

  /** Delete an entry. */
  remove(id) {
    return http.delete(`/world-info/entry/${id}`)
  },
}
