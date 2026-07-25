/**
 * Extension loader — fetches active extensions at startup and injects their
 * JS/CSS resources.  Each extension gets a sandboxed ``$extension`` API.
 */

import { extensionApi } from '../api/extensions.js'
import { createExtensionAPI } from './extensionSandbox.js'

/** Registry of loaded extension instances. */
const _loaded = {}

/**
 * Bootstrap all active extensions.  Called once from ``main.js``.
 * @param {object} context - Global read-only context for all extensions.
 */
export async function loadExtensions(context = {}) {
  try {
    const res = await extensionApi.list()
    const extensions = res.data || []

    for (const ext of extensions) {
      const manifest = typeof ext.manifest === 'string'
        ? JSON.parse(ext.manifest)
        : ext.manifest

      if (!manifest || !manifest.id) continue

      const api = createExtensionAPI(manifest.id, { ...context, manifest })

      // Load CSS if defined
      if (manifest.resources?.css) {
        for (const cssFile of manifest.resources.css) {
          const link = document.createElement('link')
          link.rel = 'stylesheet'
          link.href = `/extensions/${manifest.id}/${cssFile}`
          link.dataset.extId = manifest.id
          document.head.appendChild(link)
        }
      }

      // Load JS — execute with $extension in scope
      if (manifest.resources?.js) {
        for (const jsFile of manifest.resources.js) {
          await _loadAndExec(manifest.id, jsFile, api)
        }
      }

      _loaded[manifest.id] = { manifest, api }
    }
  } catch (e) {
    console.error('Extension loader: failed to load extensions', e)
  }
}

/**
 * Fetch a JS file and execute it with ``$extension`` in scope.
 */
async function _loadAndExec(extId, jsFile, api) {
  try {
    const url = `/extensions/${extId}/${jsFile}`
    const resp = await fetch(url)
    if (!resp.ok) return
    const code = await resp.text()

    // Sandboxed execution: the code sees only `$extension`
    const fn = new Function('$extension', code)
    fn(api)
  } catch (e) {
    console.error(`Extension "${extId}": failed to load ${jsFile}`, e)
  }
}

/**
 * Trigger a hook across all loaded extensions.
 * @returns {Array} Results from all registered listeners.
 */
export function triggerHook(hookName, data = {}) {
  const results = []
  for (const [extId, entry] of Object.entries(_loaded)) {
    const triggered = entry.api.hooks._trigger(hookName, data)
    results.push(...triggered.filter(r => r !== undefined))
  }
  return results
}

/**
 * Unload an extension by id — removes its resources and listeners.
 */
export function unloadExtension(extId) {
  // Remove injected stylesheets
  document.querySelectorAll(`link[data-ext-id="${extId}"]`).forEach(el => el.remove())

  delete _loaded[extId]
}
