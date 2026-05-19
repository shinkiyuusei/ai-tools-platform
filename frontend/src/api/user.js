import http from './http'

export const sendCode = (data) => http.post('/user/sendCode', data)
export const register = (data) => http.post('/user/register', data)
export const login = (data) => http.post('/user/login', data)
export const resetPassword = (data) => http.post('/user/resetPassword', data)
export const getUserInfo = () => http.get('/user/info')
export const updateUserInfo = (data) => http.post('/user/info/update', data)
export const getRecordList = (params) => http.get('/user/record/list', { params })
export const collectRecord = (recordId) => http.post('/user/record/collect', { recordId })
export const collectTool = (toolId) => http.post('/user/tool/collect', { toolId })
export const getCollectedStatus = (toolId) => http.get(`/user/tool/collect/${toolId}`)
export const getCollectedTools = (params) => http.get('/user/tool/collected', { params })
export const getRecentTools = (params) => http.get('/user/tool/recent', { params })
