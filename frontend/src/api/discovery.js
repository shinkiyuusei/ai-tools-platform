import http from './http'

export const discoveryApi = {
  getRecommend(params) {
    return http.get('/discovery/recommend', { params })
  },
  getCategories() {
    return http.get('/discovery/categories')
  },
}
