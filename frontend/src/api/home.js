import http from './http'

export const getHomeIndex = () => http.get('/home/index')
export const searchTools = (keyword) => http.get('/tool/search', { params: { keyword } })
