/**
 * Shared message rendering utilities for immersive chat.
 *
 * Transforms raw AI response text into styled HTML with:
 *   - Inner thoughts  （...） → <span class="inner-thought">
 *   - Dialogue       "..."  → <span class="dialogue">
 *   - Status section 【角色状态栏】 → extracted separately
 */

/**
 * Escape HTML entities to prevent XSS when using v-html.
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/**
 * Wrap inner-thought patterns （...） with styled spans.
 * Matches full-width parentheses and their contents.
 */
function wrapInnerThoughts(html) {
  return html.replace(/（([^）]*)）/g, '<span class="inner-thought">（$1）</span>')
}

/**
 * Wrap dialogue patterns "..." (full-width Chinese quotes) with styled spans.
 * Uses Unicode ranges for Chinese quotation marks U+201C and U+201D.
 */
function wrapDialogue(html) {
  // Full-width Chinese left/right double quotes
  return html.replace(/“([^”]*)”/g, '<span class="dialogue">“$1”</span>')
}

/**
 * Parse a single field line like "服装：水手服" or "好感度：55（+5）"
 */
function parseFieldLine(line) {
  const match = line.match(/^([^：:]+)[：:]\s*(.+)$/)
  if (!match) return null
  const key = match[1].trim()
  let value = match[2].trim()

  const numMatch = value.match(/^(\d+(?:\.\d+)?)\s*(?:[（(]\s*([+-]?\d+)\s*[）)])?/)
  if (numMatch) {
    return {
      key,
      entry: {
        value: parseFloat(numMatch[1]),
        delta: numMatch[2] ? parseInt(numMatch[2], 10) : 0,
        raw: value,
        type: 'number',
      },
    }
  }
  return { key, entry: { value, raw: value, type: 'text' } }
}

/**
 * Check if a line looks like a character name header (short, no colon).
 */
function isCharNameHeader(line) {
  return line.trim() && !/[：:]/.test(line) && line.trim().length <= 20
}

/**
 * Extract the 【角色状态栏】 section from content.
 *
 * Supports both multi-character and single-character formats.
 * Returns status data or null.
 */
export function extractStatusSection(content) {
  if (!content) return null
  const marker = '【角色状态栏】'
  const idx = content.indexOf(marker)
  if (idx === -1) return null

  // Extract from marker to the next 【 marker or end of string
  let section = content.slice(idx + marker.length)
  const nextMarker = section.indexOf('【')
  if (nextMarker !== -1) {
    section = section.slice(0, nextMarker)
  }

  const lines = section.split('\n')

  // Detect multi-character format: has short lines without colon (role name headers)
  const hasRoleHeaders = lines.some((l) => isCharNameHeader(l))

  if (hasRoleHeaders) {
    // Multi-character format
    const result = {}
    let currentChar = null
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      if (isCharNameHeader(trimmed)) {
        currentChar = trimmed
        if (!result[currentChar]) result[currentChar] = {}
        continue
      }
      if (currentChar) {
        const parsed = parseFieldLine(trimmed)
        if (parsed) {
          result[currentChar][parsed.key] = parsed.entry
        }
      }
    }
    return Object.keys(result).length > 0 ? result : null
  }

  // Single-character format (legacy)
  const result = {}
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    const parsed = parseFieldLine(trimmed)
    if (parsed) {
      result[parsed.key] = parsed.entry
    }
  }
  return Object.keys(result).length > 0 ? result : null
}

/**
 * Remove the 【角色状态栏】 section from display text.
 */
export function stripStatusSection(content) {
  if (!content) return content
  const marker = '【角色状态栏】'
  const idx = content.indexOf(marker)
  if (idx === -1) return content
  let before = content.slice(0, idx)
  // Also strip any trailing 【抉择分支】 section (for ChatView)
  // but only the status bar is stripped here; choices are handled by ChatView's existing logic
  return before.trimEnd()
}

/**
 * Parse immersive content: escape HTML, convert newlines, wrap inner thoughts and dialogue.
 *
 * @param {string} content - Raw AI response text
 * @param {object} options
 * @param {boolean} options.stripStatus - Whether to remove the status section from display text (default true)
 * @returns {{ html: string, statusData: object|null }}
 */
export function parseImmersiveContent(content, options = {}) {
  const { stripStatus = true } = options
  if (!content) return { html: '', statusData: null }

  // Extract status section first (before HTML escaping)
  const statusData = extractStatusSection(content)

  // Remove status section from display if requested
  let displayText = stripStatus ? stripStatusSection(content) : content

  // Escape HTML
  let html = escapeHtml(displayText)

  // Convert newlines to <br>
  html = html.replace(/\n/g, '<br>')

  // Wrap inner thoughts and dialogue
  html = wrapInnerThoughts(html)
  html = wrapDialogue(html)

  return { html, statusData }
}

/**
 * Simple format: just convert newlines to <br> (backward-compatible fallback).
 */
export function formatContentSimple(content) {
  if (!content) return ''
  return escapeHtml(content).replace(/\n/g, '<br>')
}
