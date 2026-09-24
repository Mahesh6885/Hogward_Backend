/**
 * HOGWARTS LEGACY 5.0 — Security Module
 * - Login attempt tracking + lockout
 * - Session timeout with modal
 * - Input sanitization
 * - Duplicate request prevention
 */

import { toast } from './toast.js';

// ── Constants ────────────────────────────────────────────────────────────────
const MAX_ATTEMPTS    = 5;
const LOCKOUT_MS      = 15 * 60 * 1000;   // 15 minutes
const SESSION_IDLE_MS = 30 * 60 * 1000;   // 30 minutes
const WARN_BEFORE_MS  = 60 * 1000;        // warn 60s before expiry
const ATTEMPTS_KEY    = 'hw_login_attempts';
const LOCKOUT_KEY     = 'hw_lockout_until';

// ── Login Attempt Tracking ───────────────────────────────────────────────────
export const loginSecurity = {
  getAttempts() {
    return parseInt(localStorage.getItem(ATTEMPTS_KEY) || '0', 10);
  },

  getLockoutUntil() {
    return parseInt(localStorage.getItem(LOCKOUT_KEY) || '0', 10);
  },

  isLocked() {
    const until = this.getLockoutUntil();
    if (until && Date.now() < until) return true;
    if (until && Date.now() >= until) {
      // Lockout expired — clear it
      localStorage.removeItem(LOCKOUT_KEY);
      localStorage.removeItem(ATTEMPTS_KEY);
    }
    return false;
  },

  getRemainingLockoutMs() {
    return Math.max(0, this.getLockoutUntil() - Date.now());
  },

  getRemainingLockoutFormatted() {
    const ms   = this.getRemainingLockoutMs();
    const mins = Math.ceil(ms / 60000);
    return `${mins} minute${mins !== 1 ? 's' : ''}`;
  },

  recordFailure() {
    const attempts = this.getAttempts() + 1;
    localStorage.setItem(ATTEMPTS_KEY, attempts);
    if (attempts >= MAX_ATTEMPTS) {
      const until = Date.now() + LOCKOUT_MS;
      localStorage.setItem(LOCKOUT_KEY, until);
    }
    return attempts;
  },

  recordSuccess() {
    localStorage.removeItem(ATTEMPTS_KEY);
    localStorage.removeItem(LOCKOUT_KEY);
  },

  attemptsLeft() {
    return Math.max(0, MAX_ATTEMPTS - this.getAttempts());
  },
};

// ── Input Sanitization ───────────────────────────────────────────────────────
export function sanitizeInput(value) {
  if (typeof value !== 'string') return '';
  // Trim whitespace
  let s = value.trim();
  // Basic XSS prevention — escape HTML special chars
  s = s.replace(/&/g, '&amp;')
       .replace(/</g, '&lt;')
       .replace(/>/g, '&gt;')
       .replace(/"/g, '&quot;')
       .replace(/'/g, '&#x27;')
       .replace(/\//g, '&#x2F;');
  return s;
}

export function sanitizeForDisplay(value) {
  if (typeof value !== 'string') return '';
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Raw text for API — only trim, don't HTML-encode
export function cleanForApi(value) {
  return typeof value === 'string' ? value.trim() : '';
}

// ── Debounce / Duplicate Prevention ─────────────────────────────────────────
export function preventDuplicate(btn, asyncFn, loadingText = 'Processing…') {
  let pending = false;
  return async function (...args) {
    if (pending) return;
    pending = true;
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="hw-spinner"></span>${loadingText}`;
    try {
      await asyncFn(...args);
    } finally {
      pending = false;
      btn.disabled = false;
      btn.innerHTML = origText;
    }
  };
}

// ── Password Strength Meter ──────────────────────────────────────────────────
export function checkPasswordStrength(password) {
  let score = 0;
  const checks = {
    length:    password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number:    /[0-9]/.test(password),
    special:   /[^A-Za-z0-9]/.test(password),
  };

  score = Object.values(checks).filter(Boolean).length;

  const levels = ['', 'Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];
  const colors = ['', '#ef4444', '#ef4444', '#D4AF37', '#22c55e', '#4f8ef7'];
  const pct    = ['', '20%', '40%', '60%', '80%', '100%'];

  return {
    score,
    label: levels[score] || '',
    color: colors[score] || '',
    percent: pct[score] || '0%',
    checks,
    isValid: checks.length && score >= 3,
  };
}

export function renderPasswordStrength(container, password) {
  const s = checkPasswordStrength(password);
  container.innerHTML = `
    <div class="pw-strength-bar-wrap">
      <div class="pw-strength-bar-fill" style="width:${s.percent};background:${s.color}"></div>
    </div>
    <div class="pw-strength-meta">
      <span class="pw-strength-label" style="color:${s.color}">${s.label}</span>
      <div class="pw-strength-checks">
        ${renderCheck(s.checks.length,    '8+ chars')}
        ${renderCheck(s.checks.uppercase, 'Uppercase')}
        ${renderCheck(s.checks.lowercase, 'Lowercase')}
        ${renderCheck(s.checks.number,    'Number')}
        ${renderCheck(s.checks.special,   'Special')}
      </div>
    </div>
  `;
  return s;
}

function renderCheck(ok, label) {
  return `<span class="pw-check ${ok ? 'ok' : ''}">${ok ? '✓' : '○'} ${label}</span>`;
}

// ── Session Timeout Manager ──────────────────────────────────────────────────
export class SessionManager {
  constructor(onExpire, onWarning) {
    this.onExpire   = onExpire;
    this.onWarning  = onWarning;
    this.idleTimer  = null;
    this.warnTimer  = null;
    this.warned     = false;
    this._bound     = this._resetTimer.bind(this);
    this._modalEl   = null;
    this._countdownInterval = null;
  }

  start() {
    this._setupModal();
    this._attachListeners();
    this._resetTimer();
  }

  stop() {
    clearTimeout(this.idleTimer);
    clearTimeout(this.warnTimer);
    clearInterval(this._countdownInterval);
    this._removeListeners();
  }

  _attachListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach(e => document.addEventListener(e, this._bound, { passive: true }));
  }

  _removeListeners() {
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach(e => document.removeEventListener(e, this._bound));
  }

  _resetTimer() {
    if (this.warned) {
      // User interacted — dismiss warning
      this._hideModal();
      this.warned = false;
    }
    clearTimeout(this.idleTimer);
    clearTimeout(this.warnTimer);

    // Set warning before expiry
    this.warnTimer = setTimeout(() => {
      this.warned = true;
      this._showModal();
    }, SESSION_IDLE_MS - WARN_BEFORE_MS);

    // Hard expiry
    this.idleTimer = setTimeout(() => {
      this._hideModal();
      this.onExpire();
    }, SESSION_IDLE_MS);
  }

  _setupModal() {
    if (document.getElementById('session-timeout-modal')) return;
    const modal = document.createElement('div');
    modal.id = 'session-timeout-modal';
    modal.className = 'hw-session-modal hidden';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-labelledby', 'session-modal-title');
    modal.innerHTML = `
      <div class="hw-session-modal-box">
        <div class="hw-session-modal-icon">⏳</div>
        <h2 id="session-modal-title" class="hw-session-modal-title">Session Expiring</h2>
        <p class="hw-session-modal-body">
          Your magical session will expire in <strong id="session-countdown">60</strong> seconds due to inactivity.
        </p>
        <div class="hw-session-modal-actions">
          <button id="session-continue-btn" class="btn btn-primary">✨ Continue Session</button>
          <button id="session-logout-btn"   class="btn btn-ghost">Logout</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('session-continue-btn').addEventListener('click', () => {
      this._hideModal();
      this.warned = false;
      this._resetTimer();
    });

    document.getElementById('session-logout-btn').addEventListener('click', () => {
      this._hideModal();
      this.onExpire();
    });

    this._modalEl = modal;
  }

  _showModal() {
    if (!this._modalEl) return;
    let countdown = Math.ceil(WARN_BEFORE_MS / 1000);
    document.getElementById('session-countdown').textContent = countdown;
    this._modalEl.classList.remove('hidden');
    clearInterval(this._countdownInterval);
    this._countdownInterval = setInterval(() => {
      countdown--;
      const el = document.getElementById('session-countdown');
      if (el) el.textContent = countdown;
      if (countdown <= 0) clearInterval(this._countdownInterval);
    }, 1000);
  }

  _hideModal() {
    if (!this._modalEl) return;
    this._modalEl.classList.add('hidden');
    clearInterval(this._countdownInterval);
  }
}

// ── Remember Me ──────────────────────────────────────────────────────────────
const REMEMBER_KEY = 'hw_remembered_username';

export function saveRememberedUsername(username) {
  localStorage.setItem(REMEMBER_KEY, username);
}

export function getRememberedUsername() {
  return localStorage.getItem(REMEMBER_KEY) || '';
}

export function clearRememberedUsername() {
  localStorage.removeItem(REMEMBER_KEY);
}

// ── Secure Logout ────────────────────────────────────────────────────────────
export function secureLogout(keepRemembered = false) {
  const remembered = keepRemembered ? getRememberedUsername() : null;

  // Clear all auth-related storage
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
  sessionStorage.clear();

  // Restore remembered username if applicable
  if (remembered) {
    localStorage.setItem(REMEMBER_KEY, remembered);
  }
}
