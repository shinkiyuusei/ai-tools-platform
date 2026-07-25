/**
 * Example Extension — demonstrates the $extension API.
 *
 * This extension appends a small note after each AI message in the chat.
 * It uses the "chat.message.after" hook and reads user config.
 */

(async function () {
  const config = await $extension.config.get();

  if (!config.enabled) return;

  $extension.hooks.on('chat.message.after', (ctx) => {
    // ctx contains: { message: { role, content }, conversation, work }
    if (ctx.message?.role !== 'assistant') return;

    const prefix = config.notePrefix || '💡';
    const note = `${prefix} 字数: ~${ctx.message.content?.length || 0}`;

    // Use the UI toast as a non-invasive notification
    // (in a real extension you'd inject into the DOM via a registered component)
    $extension.ui.toast(note, 'info');
  });

  // Store a greeting in isolated storage
  const greeting = await $extension.storage.get('greeting');
  if (!greeting) {
    await $extension.storage.set('greeting', `Hello from ${$extension.context.manifest?.name?.zh || 'extension'}!`);
  }
})();
