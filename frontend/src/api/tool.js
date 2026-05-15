import http from './http'

export const getToolList = (params) => http.get('/tool/list', { params })
export const getToolDetail = (toolId) => http.get(`/tool/detail/${toolId}`)
export const generateByTool = (toolId, payload) => http.post(`/ai/generate/${toolId}`, payload)
