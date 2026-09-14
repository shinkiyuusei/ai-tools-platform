import assert from 'node:assert/strict'
import test from 'node:test'

import { providerDisplayName } from '../src/utils/aiProvider.js'

test('uses the provider name returned by the API for dropdown text', () => {
  assert.equal(providerDisplayName({ key: '27api', name: '27 API' }), '27 API')
})

test('uses the provider key when a legacy provider has no name', () => {
  assert.equal(providerDisplayName({ key: 'wangyou', name: '' }), 'wangyou')
})
