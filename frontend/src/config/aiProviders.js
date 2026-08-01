/**
 * Shared AI provider / model registry used by chat views.
 */
export const aiProviders = [
  {
    key: 'deepseek',
    label: 'DeepSeek',
    models: [
      { key: 'deepseek-v4-flash', label: 'DeepSeek Flash' },
      { key: 'deepseek-v4-pro', label: 'DeepSeek Pro' },
    ],
  },
  {
    key: 'gemini',
    label: 'Gemini',
    models: [
      { key: '[YDE]gemini-3.1-flash-防截断-0.5', label: 'Gemini 3.1 Flash (YDE)' },
    ],
  },
]
