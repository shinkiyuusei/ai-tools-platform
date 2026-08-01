import { defineStore } from 'pinia'
import { ref } from 'vue'

let toastId = 0

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function show(message, type = 'error', duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }

  function dismiss(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function error(message, duration) {
    return show(message, 'error', duration)
  }

  function success(message, duration) {
    return show(message, 'success', duration ?? 2000)
  }

  function info(message, duration) {
    return show(message, 'info', duration)
  }

  return { toasts, show, dismiss, error, success, info }
})
