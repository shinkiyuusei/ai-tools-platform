import http from './http'

export const register = (data) => http.post('/user/register', data)
export const login = (data) => http.post('/user/login', data)
export const resetPassword = (data) => http.post('/user/resetPassword', data)
export const getUserInfo = () => http.get('/user/info')
export const updateUserInfo = (data) => http.post('/user/info/update', data)
