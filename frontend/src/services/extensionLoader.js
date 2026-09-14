/** Load untrusted extensions inside opaque-origin sandboxed iframes. */
import { extensionApi } from '../api/extensions.js'
import { createExtensionAPI, invokeExtensionAPI } from './extensionSandbox.js'

const loaded = {}

const sandboxDocument = `<!doctype html><meta charset="utf-8"><script>
  const pending = new Map(); let nextId = 0; const hooks = new Map();
  const send = (message) => parent.postMessage(message, '*');
  const call = (method, args) => new Promise((resolve, reject) => {
    const id = ++nextId; pending.set(id, { resolve, reject });
    send({ type: 'extension:call', id, method, args });
  });
  const api = (context) => ({
    hooks: {
      on(name, callback) { if (typeof callback !== 'function') throw new TypeError('hook callback must be a function'); const id = ++nextId; const items = hooks.get(name) || new Map(); items.set(id, callback); hooks.set(name, items); send({ type: 'extension:hook:add', name, id }); return id; },
      off(name, id) { hooks.get(name)?.delete(id); send({ type: 'extension:hook:remove', name, id }); },
    },
    ui: { toast: (message, type) => call('ui.toast', [message, type]), registerComponent: (slot, props) => call('ui.registerComponent', [slot, props]) },
    http: { get: (url, headers) => call('http.get', [url, headers]), post: (url, body, headers) => call('http.post', [url, body, headers]) },
    storage: { get: (key) => call('storage.get', [key]), set: (key, value) => call('storage.set', [key, value]) },
    config: { get: () => call('config.get', []) }, context: Object.freeze(context),
  });
  addEventListener('message', async (event) => {
    const data = event.data || {};
    if (data.type === 'extension:result') { const item = pending.get(data.id); if (!item) return; pending.delete(data.id); data.ok ? item.resolve(data.value) : item.reject(new Error(data.error || 'Extension API failed')); return; }
    if (data.type === 'extension:hook:run') { for (const callback of hooks.get(data.name)?.values() || []) { try { await callback(data.payload); } catch (error) { console.error('Extension hook failed', error); } } return; }
    if (data.type !== 'extension:init') return;
    for (const css of data.styles || []) { const style = document.createElement('style'); style.textContent = css; document.head.append(style); }
    try { new Function('$extension', data.code)(api(data.context || {})); send({ type: 'extension:ready' }); } catch (error) { send({ type: 'extension:error', error: String(error?.message || error) }); }
  });
</script>`

function createFrame() {
  const frame = document.createElement('iframe')
  frame.hidden = true
  frame.sandbox.add('allow-scripts')
  frame.srcdoc = sandboxDocument
  document.body.append(frame)
  return new Promise((resolve) => frame.addEventListener('load', () => resolve(frame), { once: true }))
}

async function fetchResource(extId, resource) {
  const response = await fetch(`/extensions/${encodeURIComponent(extId)}/${resource}`)
  if (!response.ok) throw new Error(`Unable to load extension resource: ${resource}`)
  return response.text()
}

function attachBridge(entry) {
  const onMessage = async (event) => {
    if (event.source !== entry.frame.contentWindow || !event.data?.type?.startsWith('extension:')) return
    const data = event.data
    if (data.type === 'extension:hook:add') entry.hooks.set(data.id, data.name)
    if (data.type === 'extension:hook:remove') entry.hooks.delete(data.id)
    if (data.type !== 'extension:call') return
    try {
      const value = await invokeExtensionAPI(entry.api, data.method, data.args)
      entry.frame.contentWindow.postMessage({ type: 'extension:result', id: data.id, ok: true, value }, '*')
    } catch (error) {
      entry.frame.contentWindow.postMessage({ type: 'extension:result', id: data.id, ok: false, error: String(error?.message || error) }, '*')
    }
  }
  window.addEventListener('message', onMessage)
  return () => window.removeEventListener('message', onMessage)
}

export async function loadExtensions(context = {}) {
  try {
    const res = await extensionApi.list()
    for (const ext of res.data || []) {
      const manifest = typeof ext.manifest === 'string' ? JSON.parse(ext.manifest) : ext.manifest
      if (!manifest?.id || loaded[manifest.id]) continue
      const [code, styles] = await Promise.all([
        Promise.all((manifest.resources?.js || []).map((file) => fetchResource(manifest.id, file))).then((files) => files.join('\n')),
        Promise.all((manifest.resources?.css || []).map((file) => fetchResource(manifest.id, file))),
      ])
      const frame = await createFrame()
      const entry = { manifest, api: createExtensionAPI(manifest.id, { ...context, manifest }), frame, hooks: new Map() }
      entry.detach = attachBridge(entry)
      frame.contentWindow.postMessage({ type: 'extension:init', code, styles, context: { ...context, manifest } }, '*')
      loaded[manifest.id] = entry
    }
  } catch (error) {
    console.error('Extension loader: failed to load extensions', error)
  }
}

export function triggerHook(hookName, data = {}) {
  for (const entry of Object.values(loaded)) {
    if ([...entry.hooks.values()].includes(hookName)) {
      entry.frame.contentWindow.postMessage({ type: 'extension:hook:run', name: hookName, payload: data }, '*')
    }
  }
}

export function unloadExtension(extId) {
  const entry = loaded[extId]
  if (!entry) return
  entry.detach()
  entry.frame.remove()
  delete loaded[extId]
}
