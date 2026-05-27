<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { chatApi, conversationApi } from '../api/chat'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../layouts/AppLayout.vue'
import { formatTokens } from '../utils/format'

const route = useRoute()
const auth = useAuthStore()
const workId = Number(route.params.workId)

const work = ref(null)
const loading = ref(true)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const selectedModel = ref('deepseek-v4-flash')
const thinkingMode = ref(false)
const activeStream = ref(null)
const currentConversationId = ref(null)
const conversationList = ref([])
const loadingHistory = ref(false)
const sceneContext = ref(null)
const selectedPerspectiveKey = ref('')
const perspectiveOptions = ref([])
const switchingPerspective = ref(false)
const favorited = ref(false)

// ---- Opening tooltip ----
const tooltipText = ref('')
const tooltipPos = ref({ x: 0, y: 0 })

function showTooltip(e, text) {
  const rect = e.currentTarget.getBoundingClientRect()
  const tooltipW = 400
  let left = rect.left - tooltipW - 20
  if (left < 16) left = rect.right + 20
  tooltipPos.value = {
    x: left,
    y: Math.max(16, rect.top),
  }
  tooltipText.value = text
}

function hideTooltip() {
  tooltipText.value = ''
}

const checkFavoriteStatus = async () => {
  try {
    const res = await chatApi.getCollectStatus(workId)
    favorited.value = res.data.collected
  } catch { /* ignore */ }
}

const toggleFavorite = async () => {
  try {
    const res = await chatApi.collectWork(workId)
    favorited.value = res.data.collected
  } catch {
    // silently fail
  }
}

const models = [
  { key: 'deepseek-v4-flash', label: 'DeepSeek Flash' },
  { key: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
]

const ensureConversation = async () => {
  if (currentConversationId.value) return
  try {
    const res = await conversationApi.create(workId, 'work', '')
    currentConversationId.value = res.data.id
    loadConversationList()
  } catch (e) {
    console.error('Failed to create conversation:', e)
  }
}

const saveMessages = async () => {
  const cid = currentConversationId.value
  if (!cid) return
  const unsaved = messages.value.filter(
    (m) => !m.streaming && !m._saved && m.content
  )
  if (!unsaved.length) return
  try {
    await conversationApi.addMessages(
      cid,
      unsaved.map((m) => ({ role: m.role, content: m.content })),
    )
    unsaved.forEach((m) => (m._saved = true))
  } catch (e) {
    console.error('Failed to save messages:', e)
  }
}

const loadConversationList = async () => {
  try {
    const res = await conversationApi.list(workId, 1, 20)
    conversationList.value = res.data.list || []
  } catch (e) {
    console.error('Failed to load conversations:', e)
  }
}

const loadConversation = async (convId) => {
  if (activeStream.value) {
    activeStream.value.cancel()
    activeStream.value = null
  }
  loadingHistory.value = true
  try {
    const res = await conversationApi.getDetail(convId)
    const conv = res.data
    if (!conv || !conv.messages) return
    currentConversationId.value = conv.id
    messages.value = conv.messages.map((m) => ({
      role: m.role,
      content: m.content,
      _saved: true,
      choices: m.role === 'assistant' ? parseChoices(m.content) : [],
    }))
    sending.value = false
    nextTick(() => scrollToBottom())
  } catch (e) {
    console.error('Failed to load conversation:', e)
  } finally {
    loadingHistory.value = false
  }
}

const loadWork = async (perspectiveKey = '') => {
  try {
    const params = perspectiveKey ? { perspective: perspectiveKey } : {}
    const res = await chatApi.getWorkConfig(workId, params)
    work.value = res.data
    buildPerspectiveOptions()
  } catch (e) {
    console.error('Failed to load work:', e)
  }
}

const buildPerspectiveOptions = () => {
  const options = []
  const protag = work.value?.protagonist
  const chars = work.value?.characters || []

  if (protag?.name) {
    options.push({
      key: '',
      label: `${protag.name}（默认）`,
    })
  }

  for (const c of chars) {
    if (!c.name) continue
    if (protag?.name && c.name === protag.name) continue
    options.push({
      key: c.name,
      label: c.name + (c.occupation ? ' · ' + c.occupation : ''),
    })
  }

  if (options.length === 0) {
    options.push({
      key: '',
      label: '主角（默认）',
    })
  }

  perspectiveOptions.value = options
}

const onPerspectiveChange = async () => {
  if (activeStream.value) {
    activeStream.value.cancel()
    activeStream.value = null
  }
  messages.value = []
  sending.value = false
  currentConversationId.value = null
  sceneContext.value = null
  inputText.value = ''

  const key = selectedPerspectiveKey.value
  try {
    switchingPerspective.value = true
    await loadWork(key)
  } catch (e) {
    console.error('Failed to switch perspective:', e)
  } finally {
    switchingPerspective.value = false
  }
}

const doStreamSend = (msgList) => {
  const sys = work.value?.systemPrompt || ''
  messages.value.push({ role: 'assistant', content: '', streaming: true })
  const rxMsg = messages.value[messages.value.length - 1]
  sending.value = true

  const stream = chatApi.sendMessageStream({
    messages: msgList,
    systemPrompt: sys,
    model: selectedModel.value,
    thinkingMode: thinkingMode.value,
    reasoningEffort: 'high',
    sceneContext: sceneContext.value,
    conversationId: currentConversationId.value,
  })

  stream.onChunk = (chunk) => {
    rxMsg.content += chunk
    scrollToBottom()
  }
  stream.onDone = async () => {
    rxMsg.streaming = false
    rxMsg.choices = parseChoices(rxMsg.content)
    sceneContext.value = extractSceneContext(rxMsg.content)
    sending.value = false
    activeStream.value = null
    scrollToBottom()
    await saveMessages()
    auth.refreshCredits()
  }
  stream.onError = async (err) => {
    rxMsg.content = `回复生成失败：${err}`
    rxMsg.error = true
    rxMsg.streaming = false
    sending.value = false
    activeStream.value = null
    await saveMessages()
  }

  activeStream.value = stream
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  nextTick(() => scrollToBottom())

  await ensureConversation()

  doStreamSend(messages.value)
}

const useOpening = async (text) => {
  if (!text || sending.value) return
  hideTooltip()
  messages.value.push({ role: 'user', content: text })
  nextTick(() => scrollToBottom())
  await ensureConversation()
  doStreamSend(messages.value)
}

const newConversation = () => {
  if (activeStream.value) {
    activeStream.value.cancel()
    activeStream.value = null
  }
  messages.value = []
  sending.value = false
  currentConversationId.value = null
  sceneContext.value = null
}

const scrollToBottom = () => {
  const el = document.querySelector('.chat-messages')
  if (el) el.scrollTop = el.scrollHeight
}

const extractSceneContext = (content) => {
  if (!content) return null
  const worldSetting = work.value?.worldSetting
  const timeMatch = content.match(/时间[：:]\s*(.+)/)
  const locationMatch = content.match(/地点[：:]\s*(.+)/)
  const sceneMatch = content.match(/场景[：:]\s*(.+)/)
  const statusMatch = content.match(/伴侣状态[：:]\s*(.+)/)
  if (!timeMatch && !locationMatch && !sceneMatch) return sceneContext.value
  return {
    time: timeMatch?.[1]?.trim() || '',
    location: locationMatch?.[1]?.trim() || '',
    scene: sceneMatch?.[1]?.trim() || '',
    worldName: worldSetting?.worldName || '',
    lastChoices: '',
  }
}

const findChoiceIndex = (content) => {
  const idx = content.indexOf('【抉择分支】')
  if (idx >= 0) return idx
  const m = content.match(/#{1,3}\s*抉择分支/)
  return m ? m.index : -1
}

const parseChoices = (content) => {
  const idx = findChoiceIndex(content)
  if (idx === -1) return []
  const after = content.slice(idx)
  const lines = after.split('\n')
  return lines
    .filter((l) => /^[A-E][.、)]/.test(l.trim()))
    .map((l) => l.trim())
}

const stripChoices = (content) => {
  const idx = findChoiceIndex(content)
  return idx >= 0 ? content.slice(0, idx).trimEnd() : content
}

const displayContent = (content) => {
  // strip choice section and collapse consecutive empty lines
  let text = stripChoices(content)
  // collapse triple-backtick code blocks to plain text
  text = text.replace(/```/g, '')
  // collapse 2+ newlines to a single newline (no blank lines)
  text = text.replace(/\n{2,}/g, '\n')
  return text.trimEnd()
}

const pickChoice = (text) => {
  if (sending.value) return
  inputText.value = text
  sendMessage()
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const deleteConversation = async (convId) => {
  try {
    await conversationApi.remove(convId)
    conversationList.value = conversationList.value.filter((c) => c.id !== convId)
    if (currentConversationId.value === convId) {
      newConversation()
    }
  } catch (e) {
    console.error('Failed to delete conversation:', e)
  }
}

onMounted(async () => {
  await loadWork()
  checkFavoriteStatus()
  if (work.value) {
    await loadConversationList()
    if (conversationList.value.length > 0) {
      await loadConversation(conversationList.value[0].id)
    }
  }
  loading.value = false
})
</script>

<template>
  <AppLayout>
    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="work" class="chat-page">
      <!-- ====== Chat Main Column ====== -->
      <div class="chat-main">
        <div class="chat-header">
          <span class="header-name">{{ work.name }}</span>
          <div class="header-actions">
            <select v-model="selectedModel" class="model-select">
              <option v-for="m in models" :key="m.key" :value="m.key">{{ m.label }}</option>
            </select>
            <select
              v-if="perspectiveOptions.length > 0"
              v-model="selectedPerspectiveKey"
              class="perspective-select"
              @change="onPerspectiveChange"
              :disabled="switchingPerspective"
            >
              <option
                v-for="p in perspectiveOptions"
                :key="p.key"
                :value="p.key"
              >{{ p.label }}</option>
            </select>
            <label class="think-toggle" title="启用思考模式，提升输出质量">
              <input type="checkbox" v-model="thinkingMode" />
              <span>思考</span>
            </label>
            <button class="btn-new" @click="newConversation" :disabled="messages.length === 0">
              新对话
            </button>
          </div>
        </div>

        <div class="chat-messages" :class="{ empty: messages.length === 0 }">
          <div v-if="messages.length === 0" class="chat-empty">
            <div class="empty-icon">◇</div>
            <p>开始一段新的对话</p>
            <p class="hint">在右侧面板选择开场白，或直接输入消息开始对话</p>
          </div>

          <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
            <div class="msg-avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</div>
            <div class="msg-body">
              <div class="msg-content" :class="{ error: msg.error, streaming: msg.streaming }">
                {{ displayContent(msg.content) }}<span v-if="msg.streaming" class="stream-cursor">|</span>
              </div>
              <div
                v-if="msg.choices && msg.choices.length"
                class="choice-buttons"
              >
                <button
                  v-for="(c, ci) in msg.choices"
                  :key="ci"
                  class="choice-btn"
                  @click="pickChoice(c)"
                >
                  {{ c }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-bar">
          <textarea
            v-model="inputText"
            :placeholder="sending ? 'AI 正在回复...' : '输入消息… Enter 发送，Shift+Enter 换行'"
            @keydown="handleKeydown"
            :disabled="sending"
            rows="2"
          />
          <button class="btn-send" @click="sendMessage" :disabled="sending || !inputText.trim()">
            <span v-if="sending">⟳</span>
            <span v-else>↑</span>
          </button>
        </div>
      </div>

      <!-- ====== Right Sidebar ====== -->
      <aside class="chat-sidebar">
        <!-- Work Info -->
        <div class="sb-card sb-work-info">
          <div class="sb-cover-wrap">
            <div class="sb-cover">
              <img v-if="work.icon && work.icon.startsWith('http')" :src="work.icon" :alt="work.name" />
              <span v-else class="cover-placeholder">{{ work.name.slice(0, 2) }}</span>
            </div>
            <button class="fav-heart-btn" :class="{ favorited }" @click.stop="toggleFavorite" :title="favorited ? '取消收藏' : '收藏'">
              {{ favorited ? '♥' : '♡' }}
            </button>
          </div>
          <h2 class="sb-name">{{ work.name }}</h2>
          <p class="sb-desc">{{ work.desc }}</p>
          <div class="sb-meta">
            <span v-if="work.author">{{ work.author }}</span>
            <span>{{ formatTokens(work.useCount) }}</span>
          </div>
        </div>

        <!-- Opening Lines -->
        <div v-if="work.openingStatements && work.openingStatements.length > 0 && messages.length === 0" class="sb-card sb-opening">
          <div class="sb-label">选择开场白</div>
          <div
            v-for="(item, idx) in work.openingStatements"
            :key="idx"
            class="opening-bubble"
            @click="useOpening(item.text)"
            @mouseenter="showTooltip($event, item.text)"
            @mouseleave="hideTooltip"
          >
            <div class="opening-label">{{ item.label }}</div>
            <div class="opening-preview">{{ item.text }}</div>
          </div>
        </div>
        <div v-else-if="work.opening && messages.length === 0" class="sb-card sb-opening">
          <div class="sb-label">开始对话</div>
          <div
            class="opening-bubble"
            @click="useOpening(work.opening)"
            @mouseenter="showTooltip($event, work.opening)"
            @mouseleave="hideTooltip"
          >
            <div class="opening-preview">{{ work.opening }}</div>
          </div>
        </div>

        <!-- Conversation History -->
        <div class="sb-card sb-history">
          <div class="sb-label">对话历史</div>
          <button class="btn-new-chat" @click="newConversation">
            <span>+</span> 新对话
          </button>
          <div
            v-for="conv in conversationList"
            :key="conv.id"
            :class="['history-item', { active: conv.id === currentConversationId }]"
            @click="loadConversation(conv.id)"
          >
            <button class="history-delete-btn" @click.stop="deleteConversation(conv.id)" title="删除对话">×</button>
            <div class="history-title">{{ conv.title || '未命名对话' }}</div>
            <div class="history-meta">{{ conv.messageCount }} 条消息 · {{ conv.updateTime?.slice(0, 10) || '' }}</div>
          </div>
          <p v-if="conversationList.length === 0" class="sb-empty-text">暂无对话记录</p>
        </div>

        <!-- Comments placeholder -->
        <div class="sb-card sb-comments">
          <div class="sb-label">评论</div>
          <p class="sb-empty-text">暂无评论</p>
        </div>
      </aside>

      <!-- Fixed-position tooltip for opening full text -->
      <Teleport to="body">
        <div
          v-if="tooltipText"
          class="opening-tooltip-overlay"
          :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }"
        >
          <div class="opening-tooltip-content">{{ tooltipText }}</div>
        </div>
      </Teleport>
    </div>

    <div v-else class="error-state"><p>作品不存在或已下架</p></div>
  </AppLayout>
</template>

<style scoped>
/* ====== Page Layout ====== */
.chat-page {
  display: flex;
  height: calc(100vh - 80px);
  gap: var(--space-lg);
}

.loading-state, .error-state {
  text-align: center; padding: 80px 20px; color: var(--text-tertiary);
}

/* ====== Chat Main ====== */
.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px var(--space-lg);
  border-bottom: 1px solid var(--border-card);
  flex-shrink: 0;
  gap: var(--space-md);
}

.header-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.model-select {
  padding: 5px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.perspective-select {
  padding: 5px 10px;
  background: var(--bg-elevated);
  border: 1px solid #f0a040;
  border-radius: var(--radius-sm);
  color: #f0a040;
  font-size: 12px;
  cursor: pointer;
  max-width: 180px;
}
.perspective-select:disabled {
  opacity: 0.5;
  cursor: wait;
}

.think-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}
.think-toggle input { cursor: pointer; margin: 0; }
.think-toggle:has(input:checked) { color: #f0a040; border-color: #f0a040; }

.btn-new {
  padding: 5px 12px;
  background: transparent;
  border: 1px solid var(--border-input);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-new:hover:not(:disabled) { color: var(--text-primary); border-color: var(--text-tertiary); }
.btn-new:disabled { opacity: 0.4; cursor: default; }

/* ====== Messages ====== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
}

.chat-messages.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-empty {
  text-align: center;
  color: var(--text-tertiary);
}

.chat-empty .empty-icon {
  font-size: 48px;
  opacity: 0.2;
  margin-bottom: var(--space-md);
}

.chat-empty p { margin: 0 0 4px; font-size: 14px; }
.chat-empty .hint { font-size: 12px; opacity: 0.6; }

.message {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.message.user .msg-avatar {
  background: linear-gradient(135deg, #5b7c99, #7b9cbf);
  color: #fff;
}

.message.assistant .msg-avatar {
  background: linear-gradient(135deg, #c95564, #eea2b4);
  color: #fff;
}

.msg-body { max-width: 72%; min-width: 0; }

.msg-content {
  padding: 10px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .msg-content {
  background: linear-gradient(135deg, #5b7c99, #7b9cbf);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .msg-content {
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.msg-content.error {
  color: var(--color-crimson-soft);
  border-color: rgba(200, 85, 84, 0.3);
}

.msg-content.streaming { padding-right: 8px; }

.choice-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
}

.choice-btn {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.choice-btn:hover {
  background: rgba(123, 156, 191, 0.1);
  border-color: var(--color-misty-blue-soft);
  color: var(--text-primary);
}

.stream-cursor {
  display: inline;
  animation: blink 1s step-end infinite;
  color: var(--color-candy-pink);
  font-weight: 700;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ====== Input Bar ====== */
.chat-input-bar {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-end;
  padding: var(--space-md) var(--space-lg);
  border-top: 1px solid var(--border-card);
  flex-shrink: 0;
}

.chat-input-bar textarea {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-input);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
}

.chat-input-bar textarea:focus {
  border-color: var(--color-misty-blue-soft);
  box-shadow: 0 0 0 3px rgba(123, 156, 191, 0.08);
}

.chat-input-bar textarea:disabled { opacity: 0.5; }

.btn-send {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--color-candy-pink), var(--color-crimson-soft));
  color: #fff;
  border: none;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.btn-send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(200, 85, 84, 0.3);
}

.btn-send:disabled { opacity: 0.4; cursor: default; }

/* ====== Right Sidebar ====== */
.chat-sidebar {
  width: 340px;
  flex-shrink: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.sb-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.sb-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

/* Work Info Card */
.sb-work-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-lg) var(--space-md);
}

.sb-cover-wrap {
  position: relative;
  margin-bottom: var(--space-sm);
}

.sb-cover {
  width: 96px;
  height: 96px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sb-cover img { width: 100%; height: 100%; object-fit: cover; }

.cover-placeholder {
  font-size: 20px;
  color: var(--text-tertiary);
  opacity: 0.5;
}

.fav-heart-btn {
  position: absolute;
  top: -8px;
  right: -30px;
  width: 42px;
  height: 42px;
  border: none;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 50%;
  color: var(--text-tertiary);
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  z-index: 1;
}

.fav-heart-btn:hover {
  background: rgba(0, 0, 0, 0.7);
  color: var(--color-crimson-soft);
}

.fav-heart-btn.favorited {
  color: var(--color-crimson-soft);
  background: rgba(200, 85, 84, 0.2);
}

.sb-name {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.sb-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.5;
  margin: 0 0 var(--space-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sb-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-sm);
  font-size: 11px;
  color: var(--text-tertiary);
}

.sb-rating-row {
  display: flex;
  justify-content: center;
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-card);
}

/* Opening Bubble */
.sb-opening {
  background: linear-gradient(135deg, rgba(238, 162, 180, 0.06), rgba(200, 85, 84, 0.04));
  border-color: rgba(238, 162, 180, 0.12);
  overflow: visible;
}

.opening-bubble {
  padding: 12px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: pre-wrap;
  margin-bottom: 8px;
  position: relative;
}

.opening-bubble:last-child {
  margin-bottom: 0;
}

.opening-bubble:hover {
  border-color: var(--color-candy-pink-soft);
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.18);
  z-index: 5;
}

.opening-label {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.opening-preview {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Fixed-position tooltip overlay */
.opening-tooltip-overlay {
  position: fixed;
  width: 400px;
  max-height: 320px;
  overflow-y: auto;
  z-index: 9999;
  pointer-events: none;
  animation: tooltipIn 0.15s ease-out;
}

@keyframes tooltipIn {
  from { opacity: 0; transform: translateX(4px); }
  to { opacity: 1; transform: translateX(0); }
}

.opening-tooltip-content {
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* Arrow pointing right toward the sidebar */
.opening-tooltip-overlay::after {
  content: '';
  position: absolute;
  right: -8px;
  top: 18px;
  width: 0;
  height: 0;
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-left: 8px solid var(--bg-card);
}


/* Conversation History */
.sb-history {
  max-height: none;
  overflow-y: visible;
}

.btn-new-chat {
  width: 100%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(238, 162, 180, 0.08);
  border: 1px dashed rgba(238, 162, 180, 0.25);
  color: var(--color-candy-pink-soft);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: var(--space-md);
  transition: all var(--transition-fast);
}

.btn-new-chat:hover {
  background: rgba(238, 162, 180, 0.14);
  border-color: var(--color-candy-pink-soft);
  color: var(--color-candy-pink);
}

.history-item {
  padding: 12px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 4px;
  position: relative;
}

.history-item .history-delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  border-radius: 50%;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: all var(--transition-fast);
}

.history-item:hover .history-delete-btn {
  display: flex;
}

.history-delete-btn:hover {
  background: var(--color-crimson-soft);
  color: #fff;
}

.history-item:hover {
  background: var(--bg-elevated);
}

.history-item.active {
  background: rgba(123, 156, 191, 0.1);
  border-left: 3px solid var(--color-misty-blue);
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 3px;
}

.history-meta {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* Comments */
.sb-comments { flex: 1; }

.sb-empty-text {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  padding: var(--space-md) 0;
  margin: 0;
}

/* ====== Responsive ====== */
@media (max-width: 900px) {
  .chat-sidebar { display: none; }
}

@media (max-width: 640px) {
  .chat-page { height: calc(100vh - 60px); }
  .chat-header { padding: 10px var(--space-md); flex-wrap: wrap; }
  .chat-messages { padding: var(--space-md); }
  .chat-input-bar { padding: var(--space-sm) var(--space-md); }
  .msg-body { max-width: 85%; }
}
</style>
