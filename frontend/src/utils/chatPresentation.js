import { parseImmersiveContent } from './messageRenderer.js'

export function extractSceneContext(content, work, previousContext = null) {
  if (!content) return null
  const timeMatch = content.match(/时间[：:]\s*(.+)/)
  const locationMatch = content.match(/地点[：:]\s*(.+)/)
  const sceneMatch = content.match(/场景[：:]\s*(.+)/)
  if (!timeMatch && !locationMatch && !sceneMatch) return previousContext
  return {
    time: timeMatch?.[1]?.trim() || '',
    location: locationMatch?.[1]?.trim() || '',
    scene: sceneMatch?.[1]?.trim() || '',
    worldName: work?.worldSetting?.worldName || '',
    lastChoices: '',
  }
}

function findChoiceIndex(content) {
  const marker = '【抉择分支】'
  const index = content.indexOf(marker)
  if (index >= 0) return index
  const heading = content.match(/#{1,3}\s*抉择分支/)
  return heading ? heading.index : -1
}

export function parseChoices(content) {
  const index = findChoiceIndex(content)
  if (index === -1) return []
  const choices = content.slice(index).split('\n')
    .filter((line) => /^[A-E][.、]/.test(line.trim()))
    .map((line) => line.trim())
  if (choices.length !== 1) return choices
  return choices[0].split(/\s*\/\s*(?=[A-E][.、])/g).map((item) => item.trim()).filter(Boolean)
}

export function renderChatContent(content) {
  const index = findChoiceIndex(content)
  let text = index >= 0 ? content.slice(0, index).trimEnd() : content
  text = text.replace(/```/g, '').replace(/\n{2,}/g, '\n').trimEnd()
  return parseImmersiveContent(text).html
}
