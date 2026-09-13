import { ref, computed, nextTick } from 'vue'
import { conversationApi } from '../api/chat'
import { getChatProviders } from '../api/admin'
import { readStream } from '../utils/sse'

// Fallback list used only when the server is unreachable (e.g. on first load
// before login). Mirrors the previous hardcoded config/aiProviders.js shape.
const FALLBACK_PROVIDERS = [
  {
    key: 'deepseek',
    name: 'DeepSeek',
    models: [
      { key: 'deepseek-v4-flash', label: 'DeepSeek Flash', isDefault: true },
      { key: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
    ],
  },
]

/**
 * Shared chat-session logic for ChatView (work) and CharacterChatView.
 *
 * Owns providers/models selection, conversation lifecycle (create/list/switch/
 * delete), message history mapping, stream cancellation and message saving.
 */
export function useChatSession({
  entityType = 'work',
  entityId = 0,
  scrollSelector = '.chat-messages',
  mapMessage = (m) => ({ role: m.role, content: m.content }),
  reloadListOnNew = false,
  onReset = null,
} = {}) {
  const messages = ref([])
  const inputText = ref('')
  const sending = ref(false)
  const selectedModel = ref('')
  const thinkingMode = ref(false)
  const aiProvider = ref('')
  const activeStream = ref(null)
  const currentConversationId = ref(null)
  const conversationList = ref([])
  const loadingHistory = ref(false)

  const providers = ref(FALLBACK_PROVIDERS)

  const currentProvider = computed(
    () => providers.value.find((p) => p.key === aiProvider.value) || providers.value[0],
  )
  const models = computed(() => currentProvider.value?.models || [])

  async function loadProviders() {
    try {
      const res = await getChatProviders()
      const list = res.data?.list || []
      if (list.length) {
        providers.value = list
        if (!aiProvider.value || !list.find((p) => p.key === aiProvider.value)) {
          aiProvider.value = list[0].key
        }
        const prov = list.find((p) => p.key === aiProvider.value) || list[0]
        const def = prov?.models?.find((m) => m.isDefault) || prov?.models?.[0]
        if (def && !selectedModel.value) {
          selectedModel.value = def.key
        }
      }
    } catch (e) {
      // Server unreachable / not logged in — keep FALLBACK_PROVIDERS
      if (!aiProvider.value) aiProvider.value = FALLBACK_PROVIDERS[0].key
      if (!selectedModel.value) selectedModel.value = FALLBACK_PROVIDERS[0].models[0].key
    }
  }

  function selectProvider(key) {
    aiProvider.value = key
    const prov = providers.value.find((p) => p.key === key)
    const def = prov?.models?.find((m) => m.isDefault) || prov?.models?.[0]
    if (def) selectedModel.value = def.key
  }

  function scrollToBottom() {
    const el = document.querySelector(scrollSelector)
    if (el) el.scrollTop = el.scrollHeight
  }

  async function ensureConversation() {
    if (currentConversationId.value) return
    try {
      const res = await conversationApi.create(entityId, entityType, '')
      currentConversationId.value = res.data.id
      loadConversationList()
    } catch (e) {
      console.error('Failed to create conversation:', e)
    }
  }

  async function loadConversationList() {
    try {
      const res = await conversationApi.list(entityId, entityType, 1, 20)
      conversationList.value = res.data.list || []
    } catch (e) {
      console.error('Failed to load conversations:', e)
    }
  }

  async function loadConversation(convId) {
    cancelStream()
    loadingHistory.value = true
    try {
      const res = await conversationApi.getDetail(convId)
      const conv = res.data
      if (!conv || !conv.messages) return
      currentConversationId.value = conv.id
      messages.value = conv.messages.map(mapMessage)
      sending.value = false
      await nextTick()
      scrollToBottom()
    } catch (e) {
      console.error('Failed to load conversation:', e)
    } finally {
      loadingHistory.value = false
    }
  }

  async function switchConversation(convId) {
    if (convId === currentConversationId.value) return
    await loadConversation(convId)
  }

  function newConversation() {
    stopStream()
    messages.value = []
    currentConversationId.value = null
    if (onReset) onReset()
    if (reloadListOnNew) loadConversationList()
  }

  async function deleteConversation(convId) {
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

  /**
   * Persist messages for the current conversation.
   * With an explicit list, saves it as-is (character chat pair);
   * otherwise saves only unsaved, non-streaming messages (work chat).
   */
  async function saveMessages(msgs = null) {
    const cid = currentConversationId.value
    if (!cid) return
    try {
      if (msgs) {
        await conversationApi.saveMessages(cid, msgs)
        return
      }
      const unsaved = messages.value.filter((m) => !m.streaming && !m._saved && m.content)
      if (!unsaved.length) return
      await conversationApi.addMessages(cid, unsaved.map((m) => ({ role: m.role, content: m.content })))
      unsaved.forEach((m) => (m._saved = true))
    } catch (e) {
      console.error('Failed to save messages:', e)
    }
  }

  function appendUserMessage(text) {
    messages.value.push({ role: 'user', content: text })
    inputText.value = ''
    nextTick(() => scrollToBottom())
  }

  function appendAssistantMessage({ streaming = false } = {}) {
    const msg = { role: 'assistant', content: '' }
    if (streaming) msg.streaming = true
    messages.value.push(msg)
    return msg
  }

  function cancelStream() {
    const stream = activeStream.value
    if (!stream) return
    if (typeof stream.cancel === 'function') stream.cancel()
    else if (typeof stream.abort === 'function') stream.abort()
    activeStream.value = null
  }

  function stopStream() {
    cancelStream()
    sending.value = false
  }

  return {
    messages,
    inputText,
    sending,
    selectedModel,
    thinkingMode,
    aiProvider,
    activeStream,
    currentConversationId,
    conversationList,
    loadingHistory,
    providers,
    models,
    currentProvider,
    selectProvider,
    loadProviders,
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
    cancelStream,
    stopStream,
    readStream,
  }
}
