import assert from 'node:assert/strict'
import test from 'node:test'

import { extractStatusSection } from '../src/utils/messageRenderer.js'
import { buildStatusCharacters } from '../src/utils/statusPanel.js'

const characterFields = [
  { key: '服装', label: '服装', type: 'text' },
  { key: '表情', label: '表情', type: 'text' },
  { key: '想法', label: '想法', type: 'text' },
]

test('renders a flat preset status block as one status section for a multi-character work', () => {
  const statusData = extractStatusSection(`正文\n【角色状态栏】\n服装：白色礼服\n表情：平静\n想法：观察周围`)
  const schema = {
    企业: characterFields,
    圣路易斯: characterFields,
  }

  const characters = buildStatusCharacters(schema, statusData)

  assert.equal(characters.length, 1)
  assert.equal(characters[0].name, null)
  assert.deepEqual(
    characters[0].fields.filter((field) => characters[0].data[field.key] != null).map((field) => field.key),
    ['服装', '表情', '想法'],
  )
})

test('keeps per-character status blocks separate', () => {
  const schema = { 企业: characterFields, 圣路易斯: characterFields }
  const statusData = {
    企业: { 服装: { value: '礼服', raw: '礼服', type: 'text' } },
    圣路易斯: { 表情: { value: '微笑', raw: '微笑', type: 'text' } },
  }

  assert.deepEqual(
    buildStatusCharacters(schema, statusData).map((character) => character.name),
    ['企业', '圣路易斯'],
  )
})

test('does not render schema-only characters without any status values', () => {
  const schema = { 企业: characterFields, 圣路易斯: characterFields, 赤城: characterFields }
  const statusData = {
    企业: { 表情: { value: '微笑', raw: '微笑', type: 'text' } },
  }

  assert.deepEqual(
    buildStatusCharacters(schema, statusData).map((character) => character.name),
    ['企业'],
  )
})

test('preserves nested character statuses when an AI response also contains a flat entry', () => {
  const schema = { 乙: characterFields, 丙: characterFields }
  const characters = buildStatusCharacters(schema, {
    乙: { 表情: { value: '微笑', raw: '微笑', type: 'text' } },
    旁白: { value: '雨声渐近', raw: '雨声渐近', type: 'text' },
  })

  assert.deepEqual(characters.map((character) => character.name), [null, '乙'])
  assert.equal(characters[0].data.旁白.value, '雨声渐近')
  assert.equal(characters[1].data.表情.value, '微笑')
})
