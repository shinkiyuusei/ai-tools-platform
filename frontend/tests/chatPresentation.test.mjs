import assert from 'node:assert/strict'
import test from 'node:test'

import { extractSceneContext, parseChoices } from '../src/utils/chatPresentation.js'

test('parses branch choices from an assistant response', () => {
  assert.deepEqual(
    parseChoices('正文\n【抉择分支】\nA. 前往花园\nB. 留在房间'),
    ['A. 前往花园', 'B. 留在房间'],
  )
})

test('preserves the previous scene when no scene metadata is emitted', () => {
  const previous = { time: '晚上', location: '书房', scene: '交谈', worldName: '测试', lastChoices: '' }
  assert.equal(extractSceneContext('只有叙事正文', { worldSetting: { worldName: '新世界' } }, previous), previous)
})
