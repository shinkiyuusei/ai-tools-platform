/**
 * Shared SSE reader for streaming chat responses.
 *
 * The backend streams `data: <chunk>` events separated by blank lines;
 * `[DONE]` marks completion and `[ERROR] <message>` reports failures.
 */
export async function readStream(response, { onChunk, onDone, onError } = {}) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventLines = []

  const processEvent = (data) => {
    if (data === '[DONE]') {
      onDone?.()
      return true
    }
    if (data.startsWith('[ERROR]')) {
      onError?.(data.slice(8))
      return true
    }
    onChunk?.(data)
    return false
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line === '') {
        if (eventLines.length > 0) {
          const joined = eventLines.join('\n')
          eventLines = []
          if (processEvent(joined)) return
        }
        continue
      }
      if (line.startsWith('data: ')) {
        eventLines.push(line.slice(6))
      }
    }
  }

  // Flush remaining events at stream end
  if (eventLines.length > 0) {
    const joined = eventLines.join('\n')
    if (processEvent(joined)) return
  }
  onDone?.()
}
