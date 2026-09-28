/**
 * API client — wraps fetch with auth headers and standard error handling.
 */

// Auto-detect API base URL:
// - In local dev, backend runs on localhost:8000
// - In production (PythonAnywhere), it automatically uses the current origin
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isDev ? 'http://localhost:8000' : window.location.origin;

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
 * Core fetch wrapper with timeout and robust error categorization.
 */
async function request(method, path, body = null, requireAuth = true, timeoutMs = 12000) {
  const headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache'
  };
  if (requireAuth) {
    const token = getToken();
    if (!token) {
      window.location.href = 'index.html';
      throw new Error('Not authenticated');
    }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const opts = { method, headers, cache: 'no-store' };
  if (body !== null) opts.body = JSON.stringify(body);

  // Set timeout controller
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  opts.signal = controller.signal;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, opts);
  } catch (netErr) {
    clearTimeout(timeoutId);
    if (netErr.name === 'AbortError') {
      const timeoutErr = new Error('Connection timed out. Please check your network and try again.');
      timeoutErr.isTimeout = true;
      timeoutErr.isNetwork = true;
      throw timeoutErr;
    }
    const networkErr = new Error('Unable to connect to the Ministry of Magic servers. Please check your internet connection and try again.');
    networkErr.isNetwork = true;
    networkErr.originalError = netErr;
    throw networkErr;
  } finally {
    clearTimeout(timeoutId);
  }

  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    if (requireAuth) {
      clearToken();
      window.location.href = 'index.html?expired=1';
      throw new Error('Session expired');
    } else {
      // 401 on unauthenticated route (like /login) means invalid credentials
      const extractedMsg = data.message ||
        (typeof data.detail === 'string' ? data.detail : data.detail?.message) ||
        'Incorrect username or password. Please try again.';
      const authErr = new Error(extractedMsg);
      authErr.status = 401;
      authErr.data = data;
      throw authErr;
    }
  }

  if (!res.ok) {
    let msg = data.message ||
      (typeof data.detail === 'string' ? data.detail : data.detail?.message);

    if (!msg) {
      if (res.status >= 500) {
        msg = 'The Hogwarts Portal is temporarily unavailable. Please try again in a few moments.';
      } else {
        msg = `HTTP ${res.status}`;
      }
    }

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
