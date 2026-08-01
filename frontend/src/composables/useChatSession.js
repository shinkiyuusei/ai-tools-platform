import { ref, computed, nextTick } from 'vue'
import { conversationApi } from '../api/chat'
import { aiProviders } from '../config/aiProviders'
import { readStream } from '../utils/sse'

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
  const selectedModel = ref('deepseek-v4-flash')
  const thinkingMode = ref(false)
  const aiProvider = ref('deepseek')
  const activeStream = ref(null)
  const currentConversationId = ref(null)
  const conversationList = ref([])
  const loadingHistory = ref(false)

  const providers = aiProviders

  const currentProvider = computed(
    () => providers.find((p) => p.key === aiProvider.value) || providers[0],
  )
  const models = computed(() => currentProvider.value.models)

  function selectProvider(key) {
    aiProvider.value = key
    const prov = providers.find((p) => p.key === key)
    if (prov && prov.models.length > 0) {
      selectedModel.value = prov.models[0].key
    }
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
