<script setup>

import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { characterApi } from '../api/character'
import AppLayout from '../layouts/AppLayout.vue'
import { parseImmersiveContent, extractStatusSection } from '../utils/messageRenderer'
import StatusPanel from '../components/StatusPanel.vue'
import { useChatSession } from '../composables/useChatSession'

const route = useRoute()
const router = useRouter()
const characterId = Number(route.params.id)

const character = ref(null)
const loading = ref(true)
const liked = ref(false)
const collected = ref(false)
const latestStatus = ref(null)
const statusSchema = ref([])

// ---- Shared chat session (providers, conversations, streaming) ----
const {
  messages,
  inputText,
  sending,
  selectedModel,
  thinkingMode,
  aiProvider,
  activeStream,
  currentConversationId,
  conversationList,
  providers,
  models,
  selectProvider,
  scrollToBottom,
  ensureConversation,
  loadConversationList,
  loadConversation,
  switchConversation,
  newConversation,
  deleteConversation,
  saveMessages,
  appendUserMessage,
  appendAssistantMessage,
  stopStream,
  readStream,
} = useChatSession({
  entityType: 'character',
  entityId: characterId,
  scrollSelector: '.messages-container',
  reloadListOnNew: true,
})

const loadChatConfig = async () => {
  try {
    const res = await characterApi.getChatConfig(characterId)
    statusSchema.value = res.data.statusSchema || []
    character.value = res.data
  } catch (e) {
    console.error('Failed to load character config:', e)
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  await ensureConversation()
  if (!currentConversationId.value) return

  appendUserMessage(text)
  sending.value = true

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
        aiProvider: aiProvider.value,
      }),
      signal: controller.signal,
    })

    const assistantMsg = appendAssistantMessage()

    await readStream(res, {
      onChunk: (chunk) => {
        assistantMsg.content += chunk
        scrollToBottom()
      },
      onDone: () => {},
      onError: () => {},
    })

    // Extract status from the completed assistant response
    const statusData = extractStatusSection(assistantMsg.content)
    if (statusData) {
      latestStatus.value = statusData
    }
    try {
      await saveMessages([
        { role: 'user', content: text },
        { role: 'assistant', content: assistantMsg.content },
      ])
      loadConversationList()
    } catch (e) { /* ignore */ }
  } catch (e) {
    if (e.name === 'AbortError') return
    console.error('Chat error:', e)
  } finally {
    sending.value = false
    activeStream.value = null
  }
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const toggleLike = async () => {
  try {
    const res = await characterApi.like(characterId)
    liked.value = res.data.liked
  } catch (e) { /* ignore */ }
}

const toggleCollect = async () => {
  try {
    const res = await characterApi.collect(characterId)
    collected.value = res.data.collected
  } catch (e) { /* ignore */ }
}

const viewDetail = () => {
  router.push(`/character/${characterId}`)
}

const formatContent = (content) => {
  if (!content) return ''
  const { html } = parseImmersiveContent(content)
  return html
}

onMounted(async () => {
  try {
    await loadChatConfig()
    loading.value = false
    loadConversationList()
    await ensureConversation()
    if (currentConversationId.value) {
      await loadConversation(currentConversationId.value)
    }
  } catch (e) {
    console.error('Init error:', e)
    loading.value = false
  }
})

</script>

<template>
  <AppLayout>
    <div class="chat-layout" v-if="!loading">
      <!-- Main Chat Area -->
      <div class="chat-main">
        <!-- Header -->
        <div class="chat-header">
          <div class="header-left">
            <img v-if="character?.avatar" :src="character.avatar" class="char-avatar" />
            <div v-else class="char-avatar-placeholder">{{ character?.name?.slice(0, 2) }}</div>
            <div class="char-meta">
              <h2>{{ character?.name || '角色' }}</h2>
              <span class="char-author" v-if="character?.author">— {{ character.author }}</span>
            </div>
          </div>
          <div class="header-right">
            <select v-model="aiProvider" class="provider-select" @change="selectProvider($event.target.value)">
              <option v-for="p in providers" :key="p.key" :value="p.key">{{ p.label }}</option>
            </select>
            <select v-model="selectedModel" class="model-select">
              <option v-for="m in models" :key="m.key" :value="m.key">{{ m.label }}</option>
            </select>
            <label class="think-toggle">
              <input type="checkbox" v-model="thinkingMode" />
              Thinking
            </label>
            <button
              class="btn-new-chat-header"
              @click="newConversation"
              :disabled="!messages.length"
            >新对话</button>
          </div>
        </div>

        <!-- Messages -->
        <div class="messages-container">
          <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
            <div class="msg-avatar">
              <template v-if="msg.role === 'user'">你</template>
              <template v-else>{{ character?.name?.slice(0, 2) || 'AI' }}</template>
            </div>
            <div class="msg-body">
              <div class="msg-content" v-html="formatContent(msg.content)"></div>
              <StatusPanel
                v-if="msg.role === 'assistant' && !msg.streaming && statusSchema.length"
                :status-data="extractStatusSection(msg.content)"
                :schema="statusSchema"
              />
            </div>
          </div>

          <div v-if="sending" class="message assistant">
            <div class="msg-avatar">{{ character?.name?.slice(0, 2) || 'AI' }}</div>
            <div class="msg-content typing">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
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

      <!-- Sidebar -->
      <aside class="chat-sidebar">
        <!-- Character Info -->
        <div class="sb-card sb-char-info">
          <div class="sb-cover" @click="viewDetail">
            <img v-if="character?.avatar" :src="character.avatar" :alt="character.name" />
            <div v-else class="sb-cover-placeholder">{{ character?.name?.slice(0, 2) }}</div>
          </div>
          <h2>{{ character?.name }}</h2>
          <p class="sb-desc" v-if="character?.desc">{{ character.desc }}</p>
          <p class="sb-author" v-if="character?.author">— {{ character.author }}</p>
          <div class="sb-stats">
            <span>♥ {{ character?.likeCount || 0 }}</span>
            <span>★ {{ character?.collectCount || 0 }}</span>
            <span>💬 {{ character?.useCount || 0 }}</span>
          </div>
          <div class="sb-actions">
            <button class="sb-btn" @click="toggleLike">
              {{ liked ? '♥' : '♡' }} 喜欢
            </button>
            <button class="sb-btn" @click="toggleCollect">
              {{ collected ? '★' : '☆' }} 收藏
            </button>
            <button class="sb-btn" @click="viewDetail">查看详情</button>
          </div>
        </div>

        <!-- Conversation History -->
        <div class="sb-card sb-history">
          <button class="btn-new-chat" @click="newConversation">
            <span class="plus">+</span> 新对话
          </button>
          <div class="conv-list">
            <div
              v-for="conv in conversationList"
              :key="conv.id"
              :class="['conv-item', { active: conv.id === currentConversationId }]"
              @click="switchConversation(conv.id)"
            >
              <div class="conv-info">
                <span class="conv-title">{{ conv.title || '未命名对话' }}</span>
                <span class="conv-meta">{{ conv.messageCount || 0 }} 条 · {{ formatTime(conv.createTime) }}</span>
              </div>
              <button class="conv-del" @click.stop="deleteConversation(conv.id)">×</button>
            </div>
            <div v-if="!conversationList.length" class="conv-empty">暂无对话记录</div>
          </div>
        </div>

        <!-- Comments placeholder -->
        <div class="sb-card sb-comments">
          <h3>评论</h3>
          <p class="sb-empty">暂无评论</p>
        </div>
      </aside>
    </div>
    <div v-else class="loading-state">加载中...</div>
  </AppLayout>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 64px);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ---- Sidebar ---- */
.chat-sidebar {
  width: 340px;
  flex-shrink: 0;
  border-left: 1px solid var(--border-card);
  overflow-y: auto;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  background: var(--bg-card);
}

.sb-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

/* Character info card */
.sb-cover {
  width: 96px;
  height: 96px;
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  background: var(--bg-tertiary);
  margin-bottom: var(--space-sm);
}

.sb-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sb-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: var(--text-tertiary);
}

.sb-char-info h2 {
  margin: 0 0 4px;
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.sb-desc {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin: 0 0 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sb-author {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0 0 var(--space-sm);
}

.sb-stats {
  display: flex;
  gap: var(--space-md);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.sb-actions {
  display: flex;
  gap: 6px;
}

.sb-btn {
  padding: 4px 10px;
  font-size: var(--text-xs);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.sb-btn:hover {
  border-color: var(--border-primary);
  color: var(--text-primary);
}

/* Conversation history */
.sb-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.btn-new-chat {
  width: 100%;
  padding: 8px;
  border: 1px dashed var(--border-primary);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-misty-blue-deep);
  font-size: var(--text-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-bottom: var(--space-sm);
  transition: all var(--transition-fast);
}

.btn-new-chat:hover {
  background: var(--color-misty-blue-ghost);
}

.plus {
  font-size: 16px;
  font-weight: 700;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
  border-left: 3px solid transparent;
}

.conv-item:hover {
  background: var(--bg-card);
}

.conv-item.active {
  border-left-color: var(--color-misty-blue);
  background: rgba(114, 148, 184, 0.08);
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.conv-del {
  opacity: 0;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
}

.conv-item:hover .conv-del {
  opacity: 1;
}

.conv-del:hover {
  color: var(--color-crimson);
}

.conv-empty {
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  padding: var(--space-md);
}

/* Comments */
.sb-comments {
  flex-shrink: 0;
}

.sb-comments h3 {
  margin: 0 0 var(--space-xs);
  font-size: var(--text-sm);
  color: var(--text-primary);
}

.sb-empty {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin: 0;
}

/* ---- Header ---- */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--border-card);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.char-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.char-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.char-meta h2 {
  margin: 0;
  font-size: var(--text-base);
  color: var(--text-primary);
}

.char-author {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.header-right {
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

.provider-select {
  padding: 4px 8px;
  background: var(--bg-input);
  border: 1px solid var(--color-misty-blue-deep);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--color-misty-blue-soft);
  cursor: pointer;
  font-weight: 500;
}

.think-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-new-chat-header {
  padding: 4px 12px;
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
}

.btn-new-chat-header:hover:not(:disabled) {
  border-color: var(--border-primary);
  color: var(--text-primary);
}

.btn-new-chat-header:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- Messages ---- */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.message {
  display: flex;
  gap: var(--space-sm);
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
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

/* ---- Immersive rendering: inner thoughts & dialogue ---- */
.msg-content :deep(.inner-thought) {
  color: var(--text-tertiary);
  font-style: italic;
  opacity: 0.75;
}

.msg-content :deep(.dialogue) {
  color: #e895a8;
  font-weight: 500;
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

/* ---- Input bar ---- */
.input-bar {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
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
}

.btn-send {
  background: var(--color-misty-blue-deep);
  color: #fff;
}

.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-send:hover:not(:disabled) { background: var(--color-misty-blue); }

.btn-stop {
  background: var(--color-crimson-soft);
  color: #fff;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-tertiary);
}
</style>
