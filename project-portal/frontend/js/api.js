/**
 * API client — wraps fetch with auth headers and standard error handling.
 */

const API_BASE = 'http://localhost:8000';

export function getToken() {
  return localStorage.getItem('access_token');
}

export function setToken(token) {
  localStorage.setItem('access_token', token);
}

export function clearToken() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem('user_info') || 'null');
  } catch {
    return null;
  }
}

export function setUser(user) {
  localStorage.setItem('user_info', JSON.stringify(user));
}

/**
 * Core fetch wrapper. Throws on HTTP errors.
 */
async function request(method, path, body = null, requireAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (requireAuth) {
    const token = getToken();
    if (!token) {
      window.location.href = 'index.html';
      throw new Error('Not authenticated');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const opts = { method, headers };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    clearToken();
    window.location.href = 'index.html';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const msg = data.message || data.detail || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  get:    (path, auth = true)         => request('GET',    path, null, auth),
  post:   (path, body, auth = true)   => request('POST',   path, body, auth),
  put:    (path, body, auth = true)   => request('PUT',    path, body, auth),
  patch:  (path, body, auth = true)   => request('PATCH',  path, body, auth),
  delete: (path, auth = true)         => request('DELETE', path, null, auth),
};
