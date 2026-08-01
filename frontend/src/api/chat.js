import http from './http'
import { readStream } from '../utils/sse'

const BASE = '/api/v1'

export const chatApi = {
  getWorkConfig(workId, params = {}) {
    return http.get(`/chat/work/${workId}`, { params })
  },
  getWorks(params) {
    return http.get('/chat/works', { params })
  },
  sendMessage({ messages, systemPrompt, model, thinkingMode = false, reasoningEffort = 'medium', sceneContext, conversationId, aiProvider }) {
    return http.post('/ai/chat/completions', {
      messages,
      systemPrompt,
      model,
      thinkingMode,
      reasoningEffort,
      sceneContext,
      conversationId,
      aiProvider: aiProvider || 'deepseek',
    })
  },
  async uploadCover(file) {
    const formData = new FormData()
    formData.append('file', file)
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_access_token='))
      ?.split('=')[1]
    const res = await fetch('/api/v1/chat/work/upload-cover', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...(csrfToken ? { 'X-CSRF-TOKEN': csrfToken } : {}),
      },
      body: formData,
    })
    const data = await res.json()
    if (data.code !== 0) throw new Error(data.message || '上传失败')
    return data
  },
  createWork(data) {
    return http.post('/chat/work/create', data)
  },
  updateWork(workId, data) {
    return http.put(`/chat/work/${workId}`, data)
  },
  collectWork(workId) {
    return http.post(`/chat/work/${workId}/collect`)
  },
  getCollectStatus(workId) {
    return http.get(`/chat/work/${workId}/collect`)
  },
  getCollectedWorks(params) {
    return http.get('/user/work/collected', { params })
  },
  updateWorkConfig(workId, config) {
    return http.put(`/chat/work/${workId}/config`, config)
  },
  getMyWorks(params) {
    return http.get('/user/work/my', { params })
  },
  deleteWork(workId) {
    return http.delete(`/chat/work/${workId}`)
  },
  sendMessageStream({ messages, systemPrompt, model, thinkingMode = false, reasoningEffort = 'medium', sceneContext, conversationId, aiProvider }) {
    const controller = new AbortController()

    const stream = {
      cancel() {
        controller.abort()
      },
      onChunk: null,
      onDone: null,
      onError: null,
    }

    const start = async () => {
      try {
        const csrfToken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrf_access_token='))
          ?.split('=')[1]

        const res = await fetch(`${BASE}/ai/chat/completions/stream`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            ...(csrfToken ? { 'X-CSRF-TOKEN': csrfToken } : {}),
          },
          body: JSON.stringify({ messages, systemPrompt, model, thinkingMode, reasoningEffort, sceneContext, conversationId, aiProvider: aiProvider || 'deepseek' }),
          signal: controller.signal,
        })

        if (!res.ok) {
          const err = await res.json().catch(() => ({ message: '请求失败' }))
          stream.onError?.(err.message || '请求失败')
          return
        }

        await readStream(res, {
          onChunk: (data) => stream.onChunk?.(data),
          onDone: () => stream.onDone?.(),
          onError: (msg) => stream.onError?.(msg),
        })
      } catch (e) {
        if (e.name !== 'AbortError') {
          stream.onError?.(e.message || '网络错误')
        }
      }
    }

    start()
    return stream
  },
}

export const conversationApi = {
  create(entityId, entityType = 'work', title = '') {
    return http.post('/conversation', { entityId, entityType, title })
  },
  getDetail(id) {
    return http.get(`/conversation/${id}`)
  },
  saveMessages(id, messages) {
    return http.post(`/conversation/${id}/messages`, { messages })
  },
  addMessages(id, messages) {
    return http.post(`/conversation/${id}/messages`, { messages })
  },
  list(entityId, entityType = 'work', pageNum = 1, pageSize = 20) {
    return http.get('/conversations', { params: { entityId, entityType, pageNum, pageSize } })
  },
  remove(id) {
    return http.delete(`/conversation/${id}`)
  },
}
