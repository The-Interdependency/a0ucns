const OPENAI_COMPATIBLE_DEFAULT = (modelId) => ({
  model: modelId,
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: 'Hello' },
  ],
  temperature: 0.7,
  max_tokens: 1024,
  stream: true,
});

const ANTHROPIC_DEFAULT = (modelId) => ({
  model: modelId,
  system: 'You are a helpful assistant.',
  max_tokens: 1024,
  temperature: 0.7,
  messages: [
    { role: 'user', content: 'Hello' },
  ],
  stream: true,
});

const GEMINI_DEFAULT = (modelId) => ({
  model: modelId,
  contents: [
    {
      role: 'user',
      parts: [{ text: 'Hello' }],
    },
  ],
  generationConfig: {
    temperature: 0.7,
    maxOutputTokens: 1024,
  },
});

export function getModelDefaultPayload(developerId, modelId) {
  if (developerId === 'anthropic') return ANTHROPIC_DEFAULT(modelId);
  if (developerId === 'google') return GEMINI_DEFAULT(modelId);
  return OPENAI_COMPATIBLE_DEFAULT(modelId);
}
