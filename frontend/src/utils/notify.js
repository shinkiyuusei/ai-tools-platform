import { useToastStore } from '../stores/toast'

/**
 * Shared notification helpers backed by the Pinia toast store.
 */
export function notifySuccess(msg) {
  useToastStore().success(msg)
}

export function notifyError(msg) {
  useToastStore().error(msg)
}
