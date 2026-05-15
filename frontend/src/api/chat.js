import http from './http'

const BASE = '/api/v1'

export const chatApi = {
  getWorkConfig(workId, params = {}) {
    return http.get(`/chat/work/${workId}`, { params })
  },
  getWorks(params) {
    return http.get('/chat/works', { params })
  },
  sendMessage({ messages, systemPrompt, model, thinkingMode = false, reasoningEffort = 'medium', sceneContext, conversationId }) {
    return http.post('/ai/chat/completions', {
      messages,
      systemPrompt,
      model,
      thinkingMode,
      reasoningEffort,
      sceneContext,
      conversationId,
    })
  },
  async uploadCover(file) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/v1/chat/work/upload-cover', {
      method: 'POST',
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
  updateWorkConfig(workId, config) {
    return http.put(`/chat/work/${workId}/config`, config)
  },
  sendMessageStream({ messages, systemPrompt, model, thinkingMode = false, reasoningEffort = 'medium', sceneContext, conversationId }) {
    const controller = new AbortController()
    let cancelled = false

    const stream = {
      cancel() {
        cancelled = true
        controller.abort()
      },
      onChunk: null,
      onDone: null,
      onError: null,
    }

    const start = async () => {
      try {
        const res = await fetch(`${BASE}/ai/chat/completions/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
          },
          body: JSON.stringify({ messages, systemPrompt, model, thinkingMode, reasoningEffort, sceneContext, conversationId }),
          signal: controller.signal,
        })

        if (!res.ok) {
          const err = await res.json().catch(() => ({ message: '请求失败' }))
          stream.onError?.(err.message || '请求失败')
          return
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        const processEvent = (data) => {
          if (data === '[DONE]') {
            stream.onDone?.()
            return true
          }
          if (data.startsWith('[ERROR]')) {
            stream.onError?.(data.slice(8))
            return true
          }
          stream.onChunk?.(data)
          return false
        }

        let eventLines = []

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line === '') {
              if (eventLines.length > 0) {
                const joined = eventLines.join('\n')
                eventLines = []
                if (processEvent(joined)) return
              }
              continue
            }
            if (line.startsWith('data: ')) {
              eventLines.push(line.slice(6))
            }
          }
        }
        // Flush remaining at stream end
        if (eventLines.length > 0) {
          const joined = eventLines.join('\n')
          if (processEvent(joined)) return
        }
        stream.onDone?.()
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
  create(workId, title = '') {
    return http.post('/conversation', { workId, title })
  },
  getDetail(id) {
    return http.get(`/conversation/${id}`)
  },
  addMessages(id, messages) {
    return http.post(`/conversation/${id}/messages`, { messages })
  },
  list(workId, pageNum = 1, pageSize = 20) {
    return http.get('/conversations', { params: { workId, pageNum, pageSize } })
  },
  remove(id) {
    return http.delete(`/conversation/${id}`)
  },
}
