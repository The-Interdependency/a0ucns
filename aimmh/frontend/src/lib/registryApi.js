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

export const registryApi = {
  getRegistry: () => request('/v1/registry'),
  addDeveloper: (payload) => request('/v1/registry/developer', { method: 'POST', body: JSON.stringify(payload) }),
  addModel: (developerId, payload) => request(`/v1/registry/developer/${developerId}/model`, { method: 'POST', body: JSON.stringify(payload) }),
  removeModel: (developerId, modelId) => request(`/v1/registry/developer/${developerId}/model/${modelId}`, { method: 'DELETE' }),
  removeDeveloper: (developerId) => request(`/v1/registry/developer/${developerId}`, { method: 'DELETE' }),
  verifyModel: (developerId, modelId) => request('/v1/registry/verify/model', {
    method: 'POST',
    body: JSON.stringify({ developer_id: developerId, model_id: modelId, mode: 'strict' }),
  }),
  getDefaults: () => request('/v1/registry/defaults'),
  verifyDeveloper: (developerId) => request(`/v1/registry/verify/developer/${developerId}`, { method: 'POST' }),
  verifyAll: () => request('/v1/registry/verify/all', { method: 'POST' }),
  getKeys: () => request('/v1/keys'),
  setKey: (payload) => request('/v1/keys', { method: 'POST', body: JSON.stringify(payload) }),
  removeKey: (developerId) => request(`/v1/keys/${developerId}`, { method: 'DELETE' }),
};
