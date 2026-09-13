import { computed, ref } from 'vue'
import { promptPresetApi } from '../api/promptPreset'
import { compilePrompt, generationSettings } from '../utils/promptPreset'

export function usePromptPresets() {
  const presets = ref([])
  const selectedPresetId = ref('')
  const editorOpen = ref(false)
  const selectedPreset = computed(() => presets.value.find((p) => String(p.id) === String(selectedPresetId.value)) || null)

  async function loadPresets() {
    try {
      const res = await promptPresetApi.list()
      presets.value = res.data?.list || []
      const preferred = presets.value.find((p) => p.is_default) || presets.value[0]
      if (preferred && !selectedPreset.value) selectedPresetId.value = String(preferred.id)
    } catch { presets.value = [] }
  }

  function applyPreset(basePrompt, variables) {
    return compilePrompt(selectedPreset.value?.preset, basePrompt, variables)
  }

  return { presets, selectedPresetId, selectedPreset, editorOpen, loadPresets, applyPreset,
    generationSettings: computed(() => generationSettings(selectedPreset.value?.preset)) }
}
