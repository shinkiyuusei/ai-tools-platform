<script setup>
import { computed, ref, toRaw, watch } from 'vue'
import { promptPresetApi } from '../api/promptPreset'
import { normalizePreset, orderedPrompts } from '../utils/promptPreset'

const props = defineProps({ open: Boolean, presets: { type: Array, default: () => [] }, selectedId: [String, Number] })
const emit = defineEmits(['close', 'refresh', 'select'])
const draft = ref(null)
const rawMode = ref(false)
const rawJson = ref('')
const saving = ref(false)
const fileInput = ref(null)

const promptList = computed(() => draft.value ? orderedPrompts(draft.value.preset) : [])

function clonePreset(item) {
  return structuredClone(toRaw(item))
}

watch(() => [props.open, props.selectedId, props.presets], () => {
  if (!props.open) return
  const found = props.presets.find((p) => String(p.id) === String(props.selectedId)) || props.presets[0]
  draft.value = found ? clonePreset(found) : { id: null, name: '新预设', preset: normalizePreset({}) }
  syncRaw()
}, { immediate: true, deep: true })

function syncRaw() { rawJson.value = JSON.stringify(draft.value?.preset || {}, null, 2) }
function choose(item) { emit('select', String(item.id)); draft.value = clonePreset(item); syncRaw() }
function createNew() { draft.value = { id: null, name: '新预设', preset: normalizePreset({ prompts: [] }) }; syncRaw() }

function applyRaw() {
  try { draft.value.preset = normalizePreset(JSON.parse(rawJson.value)); rawMode.value = false }
  catch { window.alert('JSON 格式不正确，请检查后重试。') }
}

function updatePrompt(prompt, field, value) {
  const original = draft.value.preset.prompts.find((p) => p.identifier === prompt.identifier)
  if (original) original[field] = value
  const order = draft.value.preset.prompt_order?.[0]?.order?.find((p) => p.identifier === prompt.identifier)
  if (field === 'enabled' && order) order.enabled = value
}

function addPrompt() {
  const identifier = crypto.randomUUID()
  draft.value.preset.prompts.push({ identifier, name: '自定义提示词', role: 'system', content: '', enabled: true, marker: false })
  if (!draft.value.preset.prompt_order.length) draft.value.preset.prompt_order.push({ character_id: 100001, order: [] })
  draft.value.preset.prompt_order[0].order.push({ identifier, enabled: true })
}

function removePrompt(prompt) {
  draft.value.preset.prompts = draft.value.preset.prompts.filter((p) => p.identifier !== prompt.identifier)
  draft.value.preset.prompt_order.forEach((group) => { group.order = (group.order || []).filter((p) => p.identifier !== prompt.identifier) })
}

async function save() {
  if (!draft.value.name.trim()) return
  saving.value = true
  try {
    if (draft.value.id) await promptPresetApi.update(draft.value.id, { name: draft.value.name, preset: draft.value.preset })
    else {
      const res = await promptPresetApi.create({ name: draft.value.name, preset: draft.value.preset })
      draft.value.id = res.data.id
    }
    emit('select', String(draft.value.id)); emit('refresh')
  } finally { saving.value = false }
}

async function setDefault() { if (draft.value?.id) { await promptPresetApi.setDefault(draft.value.id); emit('refresh') } }
async function remove() {
  if (!draft.value?.id || !window.confirm(`确定删除“${draft.value.name}”吗？`)) return
  await promptPresetApi.remove(draft.value.id); createNew(); emit('select', ''); emit('refresh')
}

function importFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      draft.value = { id: null, name: file.name.replace(/\.json$/i, ''), preset: normalizePreset(JSON.parse(reader.result)) }
      syncRaw()
    } catch { window.alert('无法读取该 JSON 预设。') }
  }
  reader.readAsText(file)
  event.target.value = ''
}

function exportFile() {
  const blob = new Blob([JSON.stringify(draft.value.preset, null, 2)], { type: 'application/json' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${draft.value.name || 'preset'}.json`; a.click(); URL.revokeObjectURL(a.href)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="preset-mask" @click.self="$emit('close')">
      <section class="preset-dialog">
        <header><h2>提示词与预设</h2><button class="icon-btn" @click="$emit('close')">×</button></header>
        <div class="preset-body">
          <aside>
            <button class="new-btn" @click="createNew">＋ 新建预设</button>
            <button v-for="item in presets" :key="item.id" :class="['preset-item', { active: String(item.id) === String(draft?.id) }]" @click="choose(item)">
              <span>{{ item.name }}</span><small v-if="item.is_default">默认</small>
            </button>
          </aside>
          <main v-if="draft">
            <div class="toolbar">
              <input v-model="draft.name" maxlength="120" placeholder="预设名称" />
              <button @click="fileInput.click()">导入 JSON</button><button @click="exportFile">导出</button>
              <input ref="fileInput" type="file" accept=".json,application/json" hidden @change="importFile" />
            </div>
            <div class="mode-tabs"><button :class="{ active: !rawMode }" @click="rawMode=false">提示词编辑器</button><button :class="{ active: rawMode }" @click="syncRaw();rawMode=true">原始 JSON</button></div>
            <template v-if="!rawMode">
              <div class="prompt-list">
                <article v-for="prompt in promptList" :key="prompt.identifier" :class="{ marker: prompt.marker }">
                  <div class="prompt-head">
                    <input :value="prompt.name || prompt.identifier" :disabled="prompt.marker" @input="updatePrompt(prompt, 'name', $event.target.value)" />
                    <select :value="prompt.role || 'system'" :disabled="prompt.marker" @change="updatePrompt(prompt, 'role', $event.target.value)"><option>system</option><option>user</option><option>assistant</option></select>
                    <label><input type="checkbox" :checked="prompt.enabled !== false" @change="updatePrompt(prompt, 'enabled', $event.target.checked)" />启用</label>
                    <button v-if="!prompt.marker" class="danger" @click="removePrompt(prompt)">删除</button>
                  </div>
                  <textarea v-if="!prompt.marker" :value="prompt.content" rows="5" placeholder="输入提示词；支持 {{char}} 和 {{user}}" @input="updatePrompt(prompt, 'content', $event.target.value)" />
                  <p v-else>结构标记：{{ prompt.identifier }}（平台会在这里注入角色/作品设定）</p>
                </article>
                <button class="add-prompt" @click="addPrompt">＋ 添加提示词</button>
              </div>
            </template>
            <div v-else class="raw-editor"><textarea v-model="rawJson" spellcheck="false" /><button @click="applyRaw">应用 JSON 修改</button></div>
          </main>
        </div>
        <footer><button class="danger" :disabled="!draft?.id" @click="remove">删除预设</button><span></span><button :disabled="!draft?.id" @click="setDefault">设为默认</button><button class="primary" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存' }}</button></footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.preset-mask{position:fixed;inset:0;z-index:10000;background:#0009;display:grid;place-items:center;padding:24px}.preset-dialog{width:min(1120px,96vw);height:min(820px,92vh);background:var(--bg-card,#17191f);color:var(--text-primary,#eee);border:1px solid var(--border-card,#444);border-radius:14px;display:flex;flex-direction:column;overflow:hidden}.preset-dialog>header,.preset-dialog>footer{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid var(--border-card,#444)}.preset-dialog>header h2{margin:0;font-size:18px}.icon-btn{margin-left:auto;font-size:25px;background:none;border:0;color:inherit}.preset-body{display:grid;grid-template-columns:230px 1fr;min-height:0;flex:1}.preset-body>aside{padding:12px;border-right:1px solid var(--border-card,#444);overflow:auto}.preset-item,.new-btn{width:100%;text-align:left;padding:10px;margin-bottom:7px;border:1px solid transparent;border-radius:8px;background:var(--bg-elevated,#242731);color:inherit;display:flex;justify-content:space-between}.preset-item.active{border-color:#7b9cbf}.preset-item small{color:#8fb9e2}.preset-body>main{padding:16px;overflow:hidden;display:flex;flex-direction:column}.toolbar,.mode-tabs,.prompt-head{display:flex;gap:8px;align-items:center}.toolbar>input{flex:1}.toolbar input,.prompt-head input,.prompt-head select{background:var(--bg-elevated,#242731);color:inherit;border:1px solid var(--border-input,#555);border-radius:6px;padding:8px}.mode-tabs{margin:12px 0}.mode-tabs button.active{color:#9cc4ed;border-color:#7b9cbf}.prompt-list{overflow:auto;padding-right:5px}.prompt-list article{border:1px solid var(--border-card,#444);border-radius:9px;padding:10px;margin-bottom:9px}.prompt-list article.marker{opacity:.72}.prompt-head>input{flex:1}.prompt-head label{white-space:nowrap}.prompt-list textarea,.raw-editor textarea{box-sizing:border-box;width:100%;margin-top:9px;padding:10px;background:#101218;color:inherit;border:1px solid var(--border-input,#555);border-radius:7px;resize:vertical}.prompt-list p{margin:8px 0 0;color:var(--text-tertiary,#999);font-size:12px}.raw-editor{display:flex;flex:1;min-height:0;flex-direction:column}.raw-editor textarea{flex:1;resize:none;font-family:monospace}.raw-editor button{align-self:flex-end;margin-top:8px}.preset-dialog button{cursor:pointer;padding:7px 11px;border-radius:6px;border:1px solid var(--border-input,#555);background:var(--bg-elevated,#242731);color:inherit}.preset-dialog button.primary{background:#547da5;border-color:#7199c0}.preset-dialog button.danger{color:#ef8d8d}.preset-dialog>footer{border-top:1px solid var(--border-card,#444);border-bottom:0}.preset-dialog>footer span{flex:1}@media(max-width:700px){.preset-mask{padding:0}.preset-dialog{width:100vw;height:100vh;border-radius:0}.preset-body{grid-template-columns:1fr}.preset-body>aside{max-height:150px;border-right:0;border-bottom:1px solid #444}.toolbar{flex-wrap:wrap}}
</style>
