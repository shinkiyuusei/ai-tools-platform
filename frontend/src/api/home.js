import http from './http'

export const getHomeIndex = () => http.get('/home/index')
