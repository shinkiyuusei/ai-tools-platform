import http from './http'

export const getCategories = (params) => http.get('/admin/category', { params })
export const createCategory = (data) => http.post('/admin/category', data)
export const updateCategory = (id, data) => http.put(`/admin/category/${id}`, data)
export const deleteCategory = (id) => http.delete(`/admin/category/${id}`)

export const getToolListAdmin = (params) => http.get('/admin/tool', { params })
export const createTool = (data) => http.post('/admin/tool', data)
export const updateTool = (id, data) => http.put(`/admin/tool/${id}`, data)
export const deleteTool = (id) => http.delete(`/admin/tool/${id}`)

export const getTagList = (params) => http.get('/admin/tag', { params })
export const createTag = (data) => http.post('/admin/tag', data)
export const updateTag = (id, data) => http.put(`/admin/tag/${id}`, data)
export const deleteTag = (id) => http.delete(`/admin/tag/${id}`)
