<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { characterApi } from '../api/character'
import { conversationApi } from '../api/chat'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../layouts/AppLayout.vue'

const route = useRoute()
const auth = useAuthStore()
const characterId = Number(route.params.id)

const character = ref(null)
const loading = ref(true)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const selectedModel = ref('deepseek-v4-flash')
const thinkingMode = ref(false)
const activeStream = ref(null)
const currentConversationId = ref(null)
const conversationList = ref([])

const models = [
  { key: 'deepseek-v4-flash', label: 'DeepSeek Flash' },
  { key: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
]

const ensureConversation = async () => {
  if (currentConversationId.value) return
  try {
    const res = await conversationApi.create(characterId, 'character', '')
    currentConversationId.value = res.data.id
  } catch (e) {
    console.error('Failed to create conversation:', e)
  }
}

const loadChatConfig = async () => {
  try {
    const res = await characterApi.getChatConfig(characterId)
    character.value = res.data
  } catch (e) {
    console.error('Failed to load character config:', e)
  }
}

const loadMessages = async () => {
  if (!currentConversationId.value) return
  try {
    const res = await conversationApi.getDetail(currentConversationId.value)
    if (res.data?.messages) {
      messages.value = res.data.messages.map(m => ({
        role: m.role,
        content: m.content,
      }))
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    console.error('Failed to load messages:', e)
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  await ensureConversation()
  if (!currentConversationId.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  sending.value = true
  await nextTick()
  scrollToBottom()

  const systemPrompt = character.value?.systemPrompt || ''
  const chatMessages = systemPrompt
    ? [{ role: 'system', content: systemPrompt }, ...messages.value]
    : [...messages.value]

  try {
    const controller = new AbortController()
    activeStream.value = controller

    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_access_token='))
      ?.split('=')[1]

    const res = await fetch('/api/v1/character/' + characterId + '/chat', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-TOKEN': csrfToken || '',
      },
      body: JSON.stringify({
        messages: chatMessages,
        model: selectedModel.value,
        thinkingMode: thinkingMode.value,
        conversationId: currentConversationId.value,
      }),
      signal: controller.signal,
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    messages.value.push({ role: 'assistant', content: '' })
    const assistantIdx = messages.value.length - 1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') continue
        if (data.startsWith('[ERROR]')) continue
        messages.value[assistantIdx].content += data
        await nextTick()
        scrollToBottom()
      }
    }

    // Save messages
    try {
      await conversationApi.saveMessages(currentConversationId.value, [
        { role: 'user', content: text },
        { role: 'assistant', content: messages.value[assistantIdx].content },
      ])
    } catch (e) { /* ignore */ }
  } catch (e) {
    if (e.name === 'AbortError') return
    console.error('Chat error:', e)
  } finally {
    sending.value = false
    activeStream.value = null
  }
}

const stopStream = () => {
  if (activeStream.value) {
    activeStream.value.abort()
    activeStream.value = null
    sending.value = false
  }
}

const scrollToBottom = () => {
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

const formatContent = (content) => {
  if (!content) return ''
  return content.replace(/\n/g, '<br>')
}

onMounted(async () => {
  try {
    await loadChatConfig()
    loading.value = false
    await ensureConversation()
    await loadMessages()
  } catch (e) {
    console.error('Init error:', e)
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <div class="character-chat" v-if="!loading">
      <!-- Header -->
      <div class="chat-header">
        <div class="character-info">
          <img v-if="character?.avatar" :src="character.avatar" class="char-avatar" />
          <div v-else class="char-avatar-placeholder">{{ character?.name?.slice(0, 2) }}</div>
          <div class="char-meta">
            <h2>{{ character?.name || '角色' }}</h2>
            <span class="char-author" v-if="character?.author">— {{ character.author }}</span>
          </div>
        </div>
        <div class="chat-controls">
          <select v-model="selectedModel" class="model-select">
            <option v-for="m in models" :key="m.key" :value="m.key">{{ m.label }}</option>
          </select>
          <label class="think-toggle">
            <input type="checkbox" v-model="thinkingMode" />
            Thinking
          </label>
        </div>
      </div>

      <!-- Messages -->
      <div class="messages-container">
        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <div class="msg-avatar">
            <template v-if="msg.role === 'user'">你</template>
            <template v-else>{{ character?.name?.slice(0, 2) || 'AI' }}</template>
          </div>
          <div class="msg-content" v-html="formatContent(msg.content)"></div>
        </div>

        <div v-if="sending" class="message assistant">
          <div class="msg-avatar">{{ character?.name?.slice(0, 2) || 'AI' }}</div>
          <div class="msg-content typing">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <!-- Input bar -->
      <div class="input-bar">
        <textarea
          v-model="inputText"
          :placeholder="'和 ' + (character?.name || '角色') + ' 聊天...'"
          rows="2"
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="sending"
        ></textarea>
        <button
          v-if="!sending"
          class="btn-send"
          @click="sendMessage"
          :disabled="!inputText.trim()"
        >发送</button>
        <button v-else class="btn-stop" @click="stopStream">停止</button>
      </div>
    </div>
    <div v-else class="loading-state">加载中...</div>
  </AppLayout>
</template>

<style scoped>
.character-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-tertiary);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--border-card);
  flex-shrink: 0;
}

.character-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.char-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.char-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.char-meta h2 {
  margin: 0;
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.char-author {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.chat-controls {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.model-select {
  padding: 4px 8px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-primary);
}

.think-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  cursor: pointer;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.message {
  display: flex;
  gap: var(--space-sm);
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 600;
  flex-shrink: 0;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.message.user .msg-avatar {
  background: var(--color-misty-blue-deep);
  color: #fff;
}

.msg-content {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1px solid var(--border-card);
}

.message.user .msg-content {
  background: var(--color-misty-blue-deep);
  color: #fff;
  border-color: transparent;
}

.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 14px 18px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: blink 1.4s infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 60%, 100% { opacity: 0.2; }
  30% { opacity: 1; }
}

.input-bar {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-md) 0;
  border-top: 1px solid var(--border-card);
  flex-shrink: 0;
}

.input-bar textarea {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-input);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-primary);
  resize: none;
  outline: none;
}

.input-bar textarea:focus {
  border-color: var(--border-focus);
}

.btn-send, .btn-stop {
  padding: 0 20px;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-send {
  background: var(--color-misty-blue-deep);
  color: #fff;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-send:hover:not(:disabled) {
  background: var(--color-misty-blue);
}

.btn-stop {
  background: var(--color-crimson-soft);
  color: #fff;
}
</style>
