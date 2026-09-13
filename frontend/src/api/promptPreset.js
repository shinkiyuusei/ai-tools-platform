import http from './http'

export const promptPresetApi = {
  list: () => http.get('/prompt-presets', { params: { pageSize: 200 } }),
  create: (data) => http.post('/prompt-presets', data),
  update: (id, data) => http.put(`/prompt-presets/${id}`, data),
  remove: (id) => http.delete(`/prompt-presets/${id}`),
  setDefault: (id) => http.post(`/prompt-presets/${id}/default`),
}
