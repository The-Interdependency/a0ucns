const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

async function request(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(`${API}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || response.statusText || 'Request failed';
    throw new Error(detail);
  }

  return data;
}

export const hubApi = {
  getModels: () => request('/v1/registry'),
  getOptions: () => request('/v1/hub/options'),
  getInstances: (includeArchived = false) => request(`/v1/hub/instances?include_archived=${includeArchived}`),
  createInstance: (payload) => request('/v1/hub/instances', { method: 'POST', body: JSON.stringify(payload) }),
  updateInstance: (instanceId, payload) => request(`/v1/hub/instances/${instanceId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  archiveInstance: (instanceId) => request(`/v1/hub/instances/${instanceId}/archive`, { method: 'POST' }),
  unarchiveInstance: (instanceId) => request(`/v1/hub/instances/${instanceId}/unarchive`, { method: 'POST' }),
  deleteInstance: (instanceId) => request(`/v1/hub/instances/${instanceId}`, { method: 'DELETE' }),
  getInstanceHistory: (instanceId, limit = 200) => request(`/v1/hub/instances/${instanceId}/history?limit=${limit}`),
  getGroups: (includeArchived = false) => request(`/v1/hub/groups?include_archived=${includeArchived}`),
  createGroup: (payload) => request('/v1/hub/groups', { method: 'POST', body: JSON.stringify(payload) }),
  updateGroup: (groupId, payload) => request(`/v1/hub/groups/${groupId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  archiveGroup: (groupId) => request(`/v1/hub/groups/${groupId}/archive`, { method: 'POST' }),
  unarchiveGroup: (groupId) => request(`/v1/hub/groups/${groupId}/unarchive`, { method: 'POST' }),
  getRuns: (includeArchived = false) => request(`/v1/hub/runs?include_archived=${includeArchived}`),
  getRunDetail: (runId) => request(`/v1/hub/runs/${runId}`),
  createRun: (payload) => request('/v1/hub/runs', { method: 'POST', body: JSON.stringify(payload) }),
  archiveRun: (runId) => request(`/v1/hub/runs/${runId}/archive`, { method: 'POST' }),
  unarchiveRun: (runId) => request(`/v1/hub/runs/${runId}/unarchive`, { method: 'POST' }),
  deleteRun: (runId) => request(`/v1/hub/runs/${runId}`, { method: 'DELETE' }),
  getChatPrompts: () => request('/v1/hub/chat/prompts'),
  getChatPrompt: (promptId) => request(`/v1/hub/chat/prompts/${promptId}`),
  sendChatPrompt: (payload) => request('/v1/hub/chat/prompts', { method: 'POST', body: JSON.stringify(payload) }),
  getSyntheses: () => request('/v1/hub/chat/syntheses'),
  getSynthesis: (batchId) => request(`/v1/hub/chat/syntheses/${batchId}`),
  createSynthesis: (payload) => request('/v1/hub/chat/synthesize', { method: 'POST', body: JSON.stringify(payload) }),
  getState: (stateKey) => request(`/v1/hub/state/${stateKey}`),
  setState: (stateKey, payload) => request(`/v1/hub/state/${stateKey}`, { method: 'PUT', body: JSON.stringify({ payload }) }),
  deleteState: (stateKey) => request(`/v1/hub/state/${stateKey}`, { method: 'DELETE' }),
  submitFeedback: (messageId, feedback) => request('/v1/a0/feedback', { method: 'POST', body: JSON.stringify({ message_id: messageId, feedback }) }),
};
