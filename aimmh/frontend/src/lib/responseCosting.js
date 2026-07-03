export function estimateTokens(text) {
  if (!text) return 0;
  return Math.ceil(String(text).length / 4);
}

export function estimateModelRate(modelId) {
  const m = (modelId || '').toLowerCase();
  if (m.includes('gpt-4o')) return 0.01;
  if (m.startsWith('o1')) return 0.015;
  if (m.includes('claude')) return 0.015;
  if (m.includes('gemini')) return 0.003;
  if (m.includes('grok')) return 0.006;
  if (m.includes('deepseek')) return 0.004;
  if (m.includes('perplexity') || m.includes('sonar')) return 0.004;
  return 0.005;
}

export function estimateResponseCostUsd(modelId, text) {
  const tokens = estimateTokens(text);
  const ratePerThousand = estimateModelRate(modelId);
  return Number(((tokens / 1000) * ratePerThousand).toFixed(6));
}
