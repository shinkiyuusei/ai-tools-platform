const BASE_MARKERS = new Set([
  'main', 'worldInfoBefore', 'personaDescription', 'charDescription',
  'charPersonality', 'scenario', 'worldInfoAfter', 'dialogueExamples', 'chatHistory',
])

export function normalizePreset(raw = {}) {
  const preset = raw && typeof raw === 'object' && !Array.isArray(raw) ? structuredClone(raw) : {}
  if (!Array.isArray(preset.prompts)) preset.prompts = []
  if (!Array.isArray(preset.prompt_order)) preset.prompt_order = []
  // SillyTavern lorebook files use an `entries` object instead of `prompts`.
  // Convert enabled constant entries into editable prompt rows while retaining
  // the original entries for lossless export and future advanced activation.
  if (!preset.prompts.length && preset.entries && typeof preset.entries === 'object') {
    const entries = Array.isArray(preset.entries) ? preset.entries : Object.values(preset.entries)
    preset.prompts = entries.filter((entry) => !entry.disable && (entry.constant || !(entry.key || []).length)).map((entry, index) => ({
      identifier: `lore-entry-${entry.uid ?? index}`,
      name: entry.comment || `世界书条目 ${index + 1}`,
      role: 'system', content: entry.content || '', enabled: true, marker: false,
    }))
    preset.prompt_order = [{ character_id: 100001, order: preset.prompts.map((p) => ({ identifier: p.identifier, enabled: true })) }]
  }
  return preset
}

export function orderedPrompts(preset) {
  const prompts = Array.isArray(preset?.prompts) ? preset.prompts : []
  const byId = new Map(prompts.map((p) => [p.identifier, p]))
  const order = preset?.prompt_order?.[0]?.order
  if (!Array.isArray(order)) return prompts
  const used = new Set()
  const result = order.map((item) => {
    used.add(item.identifier)
    const prompt = byId.get(item.identifier) || { identifier: item.identifier, name: item.identifier, marker: true }
    return { ...prompt, enabled: item.enabled !== false && prompt.enabled !== false }
  })
  prompts.forEach((p) => { if (!used.has(p.identifier)) result.push(p) })
  return result
}

function expand(text, variables) {
  return String(text || '').replace(/{{\s*(char|character|user)\s*}}/gi, (_, key) => (
    key.toLowerCase() === 'user' ? (variables.user || '用户') : (variables.char || '角色')
  ))
}

/** Compile ST prompts while inserting the platform-generated character/work prompt at its marker. */
export function compilePrompt(preset, basePrompt, variables = {}) {
  if (!preset) return basePrompt || ''
  const parts = []
  let insertedBase = false
  for (const prompt of orderedPrompts(preset)) {
    if (prompt.enabled === false) continue
    if (BASE_MARKERS.has(prompt.identifier)) {
      if (!insertedBase && ['main', 'charDescription', 'personaDescription'].includes(prompt.identifier)) {
        if (basePrompt) parts.push(basePrompt)
        insertedBase = true
      }
      continue
    }
    if (prompt.marker) continue
    const content = expand(prompt.content, variables).trim()
    if (content) parts.push(content)
  }
  if (!insertedBase && basePrompt) parts.push(basePrompt)
  return parts.join('\n\n')
}

export function generationSettings(preset) {
  if (!preset) return {}
  const number = (key, fallback) => Number.isFinite(Number(preset[key])) ? Number(preset[key]) : fallback
  return {
    temperature: number('temperature'), topP: number('top_p'), frequencyPenalty: number('frequency_penalty'),
    presencePenalty: number('presence_penalty'), maxTokens: number('openai_max_tokens'),
    reasoningEffort: preset.reasoning_effort || undefined,
  }
}
