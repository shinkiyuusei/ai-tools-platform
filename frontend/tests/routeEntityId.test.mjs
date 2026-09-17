import assert from 'node:assert/strict'
import test from 'node:test'

import { routeEntityId } from '../src/utils/routeEntityId.js'

test('preserves a bigint route parameter exactly', () => {
  const id = '11129211422117891'

  assert.equal(routeEntityId(id), id)
})
