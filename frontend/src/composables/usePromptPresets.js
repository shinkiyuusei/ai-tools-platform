import { computed, ref } from 'vue'
import { promptPresetApi } from '../api/promptPreset'
import { compilePrompt, generationSettings } from '../utils/promptPreset'
import legacyCharacterRoleplay from '../system-presets/legacy-character-roleplay.json'
import legacyInteractiveFiction from '../system-presets/legacy-interactive-fiction.json'
import legacyInteractiveFictionNsfw from '../system-presets/legacy-interactive-fiction-nsfw.json'

const SYSTEM_PRESETS = [
  {
    id: 'system:legacy-character-roleplay',
    name: '系统预设 · 旧版角色扮演',
    preset: legacyCharacterRoleplay,
    system: true,
  },
  {
    id: 'system:legacy-interactive-fiction',
    name: '系统预设 · 旧版互动小说',
    preset: legacyInteractiveFiction,
    system: true,
  },
  {
    id: 'system:legacy-interactive-fiction-nsfw',
    name: '系统预设 · 旧版互动小说 NSFW',
    preset: legacyInteractiveFictionNsfw,
    system: true,
  },
]

export function usePromptPresets() {
  const presets = ref([])
  const selectedPresetId = ref('')
  const editorOpen = ref(false)
  const selectedPreset = computed(() => presets.value.find((p) => String(p.id) === String(selectedPresetId.value)) || null)

  async function loadPresets() {
    try {
      const res = await promptPresetApi.list()
      const userPresets = res.data?.list || []
      presets.value = [...SYSTEM_PRESETS, ...userPresets]
      const preferred = userPresets.find((p) => p.is_default) || presets.value[0]
      if (preferred && !selectedPreset.value) selectedPresetId.value = String(preferred.id)
    } catch { presets.value = [] }
  }

  function applyPreset(basePrompt, variables) {
    return compilePrompt(selectedPreset.value?.preset, basePrompt, variables)
  }

  return { presets, selectedPresetId, selectedPreset, editorOpen, loadPresets, applyPreset,
    generationSettings: computed(() => generationSettings(selectedPreset.value?.preset)) }
}
