import { expect, test } from '@playwright/test'

test('empty tag form reports validation feedback instead of silently ignoring Save', async ({ page }) => {
  let createRequests = 0

  await page.route('**/api/v1/admin/tag**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: { code: 0, data: { list: [] } } })
      return
    }
    createRequests += 1
    await route.fulfill({ json: { code: 0, data: { id: 1 } } })
  })
  await page.addInitScript(() => {
    localStorage.setItem('userInfo', JSON.stringify({ vipLevel: 2 }))
  })

  await page.goto('http://127.0.0.1:4173/admin/tag')
  await page.locator('.header-row > button.base-button').click()
  await page.locator('.dialog-actions > button.base-button--primary').click()

  await expect(page.locator('.toast-error')).toContainText('请输入标签名称')
  expect(createRequests).toBe(0)
})
