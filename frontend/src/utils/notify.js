/**
 * Shared notification helpers.
 * Dispatches custom events that AppLayout listens to for toast display.
 */
export function notifySuccess(msg) {
  window.dispatchEvent(new CustomEvent('app:success', { detail: msg }))
}

export function notifyError(msg) {
  window.dispatchEvent(new CustomEvent('app:error', { detail: msg }))
}
