/**
 * Extension SFC Compiler — lightweight Node service.
 *
 * Receives .vue single-file-component source and returns compiled
 * render-function JavaScript.  Also parses manifest.yaml → JSON.
 */

const express = require('express');
const { parse: parseSFC, compileTemplate, compileScript, compileStyle } = require('@vue/compiler-sfc');
const YAML = require('yaml');

const app = express();
app.use(express.json({ limit: '2mb' }));

// ── Health ────────────────────────────────────────────────────────
app.get('/health', (_req, res) => res.json({ status: 'ok' }));

// ── Compile .vue SFC ──────────────────────────────────────────────
app.post('/compile/vue', (req, res) => {
  const { template, script, styles } = req.body || {};

  if (!template && !script) {
    return res.status(400).json({ error: 'template or script required' });
  }

  try {
    // Compose a minimal SFC for the compiler
    let sfc = '';
    if (template) sfc += `<template>${template}</template>\n`;
    if (script) sfc += `<script>${script}</script>\n`;
    if (styles && styles.length) {
      for (const s of styles) {
        const scoped = s.scoped ? ' scoped' : '';
        sfc += `<style${scoped}>${s.content || s}</style>\n`;
      }
    }

    const parsed = parseSFC(sfc, { filename: 'Component.vue' });
    const result = {};

    if (parsed.descriptor.template) {
      const compiled = compileTemplate({
        source: parsed.descriptor.template.content,
        filename: 'Component.vue',
        id: 'ext-component',
      });
      result.render = compiled.code;
    }

    if (parsed.descriptor.script || parsed.descriptor.scriptSetup) {
      const s = parsed.descriptor.scriptSetup || parsed.descriptor.script;
      const compiled = compileScript(parsed.descriptor, {
        id: 'ext-component',
      });
      result.script = compiled.content;
    }

    if (parsed.descriptor.styles.length) {
      result.styles = parsed.descriptor.styles.map(s => ({
        content: s.content,
        scoped: !!s.scoped,
      }));
    }

    res.json(result);
  } catch (err) {
    res.status(422).json({ error: `SFC compile error: ${err.message}` });
  }
});

// ── Parse manifest.yaml → JSON ─────────────────────────────────────
app.post('/parse/manifest', (req, res) => {
  const { yaml } = req.body || {};
  if (!yaml) return res.status(400).json({ error: 'yaml field required' });

  try {
    const parsed = YAML.parse(yaml);
    res.json(parsed);
  } catch (err) {
    res.status(422).json({ error: `YAML parse error: ${err.message}` });
  }
});

// ── Start ──────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3456;
app.listen(PORT, () => {
  console.log(`Extension compiler listening on port ${PORT}`);
});
