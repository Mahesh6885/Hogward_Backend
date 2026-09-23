/**
 * Authentication helpers shared across pages.
 */
import { api, setToken, setUser, clearToken, getToken, getUser } from './api.js';

export async function login(username, password) {
  const data = await api.post('/api/auth/login', { username, password }, false);
  setToken(data.data.access_token);
  setUser(data.data.user);
  return data.data.user;
}

export function logout() {
  clearToken();
  window.location.href = 'index.html';
}

export function requireAuth() {
  if (!getToken()) {
    window.location.href = 'index.html';
    return null;
  }
  return getUser();
}

export function requireAdmin() {
  const user = requireAuth();
  if (user && user.role !== 'ADMIN') {
    window.location.href = 'dashboard.html';
    return null;
  }
  return user;
}

export function requireUser() {
  const user = requireAuth();
  if (user && user.role === 'ADMIN') {
    window.location.href = 'admin.html';
    return null;
  }
  return user;
}
