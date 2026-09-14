function isStatusEntry(value) {
  return value == null
    || typeof value !== 'object'
    || Array.isArray(value)
    || 'value' in value
    || 'raw' in value
    || 'type' in value
}

function fieldsForData(schemaFields, data) {
  const fields = Array.isArray(schemaFields) ? [...schemaFields] : []
  const knownKeys = new Set(fields.map((field) => field.key))

  for (const key of Object.keys(data || {})) {
    if (!knownKeys.has(key)) {
      fields.push({ key, label: key, type: 'text' })
    }
  }
  return fields
}

/**
 * Normalize status data for StatusPanel.
 *
 * A work has a per-character schema (an object), but a prompt preset may emit
 * the legacy flat form: { 服装: entry, 表情: entry }.  Treating those field names
 * as character names produces empty sections.  Preserve the flat form as one
 * generic status section while keeping real nested character data unchanged.
 */
export function buildStatusCharacters(schema, statusData) {
  if (Array.isArray(schema)) {
    return [{ name: null, fields: fieldsForData(schema, statusData), data: statusData || {} }]
  }

  if (!schema || typeof schema !== 'object') return []

  const schemaNames = Object.keys(schema)
  const fallbackFields = schemaNames.map((name) => schema[name]).find(Array.isArray) || []
  const entries = Object.entries(statusData || {})
  const flatEntries = entries.filter(([, value]) => isStatusEntry(value))
  const nestedEntries = entries.filter(([, value]) => !isStatusEntry(value))
  const sections = []

  // Preserve malformed/mixed AI output instead of letting one flat value turn
  // every character's nested status into a generic section.
  if (flatEntries.length) {
    const flatData = Object.fromEntries(flatEntries)
    sections.push({
      name: null,
      fields: fieldsForData(fallbackFields, flatData),
      data: flatData,
    })
  }

  for (const [name, data] of nestedEntries) {
    if (!Object.keys(data || {}).length) continue
    sections.push({
      name,
      fields: fieldsForData(schema[name] || fallbackFields, data),
      data,
    })
  }
  return sections
}
