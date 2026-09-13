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

// ---- AI provider / model management ----
export const getAiProviderList = () => http.get('/admin/ai-provider')
export const createAiProvider = (data) => http.post('/admin/ai-provider', data)
export const updateAiProvider = (id, data) => http.put(`/admin/ai-provider/${id}`, data)
export const deleteAiProvider = (id) => http.delete(`/admin/ai-provider/${id}`)
export const testAiProvider = (id) => http.post(`/admin/ai-provider/${id}/test`)
export const testAiProviderDraft = (data) => http.post('/admin/ai-provider/test-connection', data)
export const fetchAiModels = (id) => http.post(`/admin/ai-provider/${id}/fetch-models`)

export const createAiModel = (data) => http.post('/admin/ai-model', data)
export const updateAiModel = (id, data) => http.put(`/admin/ai-model/${id}`, data)
export const deleteAiModel = (id) => http.delete(`/admin/ai-model/${id}`)

export const getChatProviders = () => http.get('/ai/providers')
