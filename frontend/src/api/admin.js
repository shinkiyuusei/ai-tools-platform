import http from './http'

export const getTagList = (params) => http.get('/admin/tag', { params })
export const createTag = (data) => http.post('/admin/tag', data)
export const updateTag = (id, data) => http.put(`/admin/tag/${id}`, data)
export const deleteTag = (id) => http.delete(`/admin/tag/${id}`)

export const getCharacterListAdmin = (params) => http.get('/admin/character', { params })
export const getCharacterAdmin = (id) => http.get(`/admin/character/${id}`)
export const updateCharacterAdmin = (id, data) => http.put(`/admin/character/${id}`, data)
export const deleteCharacterAdmin = (id) => http.delete(`/admin/character/${id}`)

export const getWorkListAdmin = (params) => http.get('/admin/work', { params })
export const getWorkAdmin = (id) => http.get(`/admin/work/${id}`)
export const updateWorkAdmin = (id, data) => http.put(`/admin/work/${id}`, data)
export const deleteWorkAdmin = (id) => http.delete(`/admin/work/${id}`)

export const getUserListAdmin = (params) => http.get('/admin/user', { params })
export const getUserAdmin = (id) => http.get(`/admin/user/${id}`)
export const updateUserAdmin = (id, data) => http.put(`/admin/user/${id}`, data)
export const deleteUserAdmin = (id) => http.delete(`/admin/user/${id}`)
