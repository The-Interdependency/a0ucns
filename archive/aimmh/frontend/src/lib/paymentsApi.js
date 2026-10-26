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

export const paymentsApi = {
  getCatalog: () => request('/payments/catalog'),
  getSummary: () => request('/payments/summary'),
  createCheckout: (packageId, originUrl) => request('/payments/checkout/session', { method: 'POST', body: JSON.stringify({ package_id: packageId, origin_url: originUrl }) }),
  getCheckoutStatus: (sessionId) => request(`/payments/checkout/status/${sessionId}`),
  getHall: () => request('/payments/hall-of-makers'),
  updateHallProfile: (payload) => request('/payments/hall-of-makers/profile', { method: 'PUT', body: JSON.stringify(payload) }),
};
