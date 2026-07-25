/**
 * Extension sandbox — the ``$extension`` API available to extension code.
 *
 * Extensions run in the browser but CANNOT access ``window``, ``document``,
 * raw ``fetch``, or ``localStorage`` directly.  All side effects go through
 * this sandbox, which the platform controls.
 */

import { extensionApi } from '../api/extensions.js'

/**
 * Create the sandbox API for a single extension.
 *
 * @param {string} extId   - The extension's manifest ``id``.
 * @param {object} context - Read-only context: { user, work, message, conversation }.
 * @returns {object} The ``$extension`` object.
 */
export function createExtensionAPI(extId, context = {}) {
  const _hooks = {}

  return {
    // ── hooks ─────────────────────────────────────────────────
    hooks: {
      /**
       * Register a hook listener.
       * @param {string}   hookName - e.g. "chat.message.after"
       * @param {Function} callback - Receives the hook context.
       * @returns {number} Handler id for ``off()``.
       */
      on(hookName, callback) {
        if (!_hooks[hookName]) _hooks[hookName] = []
        const id = _hooks[hookName].length
        _hooks[hookName].push({ id, callback })
        return id
      },

      /** Remove a hook listener by id. */
      off(hookName, handlerId) {
        if (!_hooks[hookName]) return
        _hooks[hookName] = _hooks[hookName].filter(h => h.id !== handlerId)
      },

      // Internal: called by the platform to fire hooks.
      _trigger(hookName, data) {
        return (_hooks[hookName] || []).map(h => {
          try { return h.callback(data) } catch (_) { return undefined }
        })
      },
    },

    // ── ui ─────────────────────────────────────────────────────
    ui: {
      /** Register a component to be rendered in a hook slot. */
      registerComponent(hookName, props = {}) {
        // Queued for the extension loader to pick up
        window.__ext_registry = window.__ext_registry || {}
        window.__ext_registry[extId] = window.__ext_registry[extId] || { components: [] }
        window.__ext_registry[extId].components.push({ hookName, props })
      },

      /** Show a toast notification. */
      toast(message, type = 'info') {
        window.dispatchEvent(new CustomEvent('app:toast', {
          detail: { message, type, source: extId },
        }))
      },
    },

    // ── http ───────────────────────────────────────────────────
    http: {
      /** GET via platform proxy (no API key exposure). */
      async get(url, headers = {}) {
        const res = await extensionApi.proxyHttp({ url, method: 'GET', headers })
        return res.data
      },
      /** POST via platform proxy. */
      async post(url, body, headers = {}) {
        const res = await extensionApi.proxyHttp({ url, method: 'POST', body, headers })
        return res.data
      },
    },

    // ── storage (isolated per extension) ────────────────────────
    storage: {
      async get(key) {
        const raw = localStorage.getItem(`ext:${extId}:${key}`)
        return raw ? JSON.parse(raw) : null
      },
      async set(key, value) {
        localStorage.setItem(`ext:${extId}:${key}`, JSON.stringify(value))
      },
    },

    // ── read-only context ───────────────────────────────────────
    context,

    // ── config ──────────────────────────────────────────────────
    config: {
      async get() {
        const res = await extensionApi.getConfig(extId)
        return res.data || {}
      },
    },
  }
}
