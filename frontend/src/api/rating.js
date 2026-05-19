import http from './http'

export const ratingApi = {
  submit(workType, workId, score) {
    return http.post('/rating', { workType, workId, score })
  },
  get(workType, workId) {
    return http.get(`/rating/${workType}/${workId}`)
  },
}
