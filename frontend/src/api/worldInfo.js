import http from './http'

export const worldInfoApi = {
  /** List all entries for an entity. */
  list(entityType, entityId) {
    return http.get('/world-info/entries', { params: { entityType, entityId } })
  },

}
