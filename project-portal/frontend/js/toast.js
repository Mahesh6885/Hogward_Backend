/**
 * HOGWARTS LEGACY 5.0 — Magical Toast Notification System
 * Replaces all browser alert() and raw .alert div usage.
 */

let toastContainer = null;
let toastQueue = [];
let activeToasts = 0;
const MAX_TOASTS = 5;

function getContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.setAttribute('aria-live', 'polite');
    toastContainer.setAttribute('aria-atomic', 'false');
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

const ICONS = {
  success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>`,
  error:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>`,
  warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>`,
  info:    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4m0-4h.01"/></svg>`,
  magic:   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 4V2m0 2v2m0-2h-2m2 0h2M3 12L1 11l2-1m0 0l1-2 1 2m-2 0l1 2M9 6l2-3 2 3-3 1zm10 9l-1 2-1-2 1-1zm-7 7l-1-2 1-1 1 1z"/></svg>`,
};

function createToast(message, type = 'info', duration = 4000) {
  if (activeToasts >= MAX_TOASTS) {
    toastQueue.push({ message, type, duration });
    return;
  }

  activeToasts++;
  const container = getContainer();
  const toast = document.createElement('div');
  toast.className = `hw-toast hw-toast-${type}`;
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status');

  toast.innerHTML = `
    <div class="hw-toast-icon">${ICONS[type] || ICONS.info}</div>
    <div class="hw-toast-body">
      <div class="hw-toast-msg">${escapeHtml(message)}</div>
    </div>
    <button class="hw-toast-close" aria-label="Dismiss notification">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
    </button>
    <div class="hw-toast-progress"><div class="hw-toast-progress-bar" style="animation-duration:${duration}ms"></div></div>
  `;

  const closeBtn = toast.querySelector('.hw-toast-close');
  closeBtn.addEventListener('click', () => dismissToast(toast));

  container.appendChild(toast);

  // Trigger entrance animation
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.add('hw-toast-visible');
    });
  });

  const timer = setTimeout(() => dismissToast(toast), duration);
  toast._timer = timer;

  return toast;
}

function dismissToast(toast) {
  if (toast._dismissed) return;
  toast._dismissed = true;
  clearTimeout(toast._timer);
  toast.classList.add('hw-toast-exit');
  toast.addEventListener('transitionend', () => {
    toast.remove();
    activeToasts = Math.max(0, activeToasts - 1);
    if (toastQueue.length > 0) {
      const next = toastQueue.shift();
      createToast(next.message, next.type, next.duration);
    }
  }, { once: true });
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(str));
  return d.innerHTML;
}

// ── Public API ──────────────────────────────────────────────────────────────
export const toast = {
  success:     (msg, duration = 4000) => createToast(`✨ Lumos: ${msg}`, 'success', duration),
  error:       (msg, duration = 5000) => createToast(`⚡ Expelliarmus: ${msg}`, 'error', duration),
  warning:     (msg, duration = 4500) => createToast(msg, 'warning', duration),
  info:        (msg, duration = 4000) => createToast(msg, 'info', duration),
  magic:       (msg, duration = 5000) => createToast(msg, 'magic', duration),

  // Signature Spell Toasts
  lumos:       (msg, duration = 4000) => createToast(`✨ Lumos: ${msg}`, 'magic', duration),
  expelliarmus:(msg, duration = 5000) => createToast(`⚡ Expelliarmus: ${msg}`, 'error', duration),
  incendio:    (msg, duration = 4500) => createToast(`🔥 Incendio: ${msg}`, 'warning', duration),
  alohomora:   (msg, duration = 4500) => createToast(`🔓 Alohomora: ${msg}`, 'magic', duration),
  colloportus: (msg, duration = 4500) => createToast(`🔒 Colloportus: ${msg}`, 'info', duration),
};

// ── Inject Styles ───────────────────────────────────────────────────────────
(function injectToastStyles() {
  if (document.getElementById('hw-toast-styles')) return;
  const style = document.createElement('style');
  style.id = 'hw-toast-styles';
  style.textContent = `
    #toast-container {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 99999;
      display: flex;
      flex-direction: column-reverse;
      gap: 0.75rem;
      pointer-events: none;
      max-width: min(400px, calc(100vw - 3rem));
    }

    .hw-toast {
      pointer-events: all;
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem 1rem 0 1rem;
      border-radius: 14px;
      backdrop-filter: blur(20px);
      border: 1px solid rgba(212, 175, 55, 0.2);
      background: rgba(15, 23, 42, 0.92);
      box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(212,175,55,0.08);
      opacity: 0;
      transform: translateX(100%) scale(0.95);
      transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      overflow: hidden;
      min-width: 280px;
      position: relative;
    }
    .hw-toast-visible {
      opacity: 1;
      transform: translateX(0) scale(1);
    }
    .hw-toast-exit {
      opacity: 0;
      transform: translateX(100%) scale(0.9);
      transition: all 0.25s ease;
    }

    .hw-toast-success { border-color: rgba(34,197,94,0.4); }
    .hw-toast-error   { border-color: rgba(239,68,68,0.4); }
    .hw-toast-warning { border-color: rgba(212,175,55,0.5); }
    .hw-toast-info    { border-color: rgba(79,142,247,0.4); }
    .hw-toast-magic   { border-color: rgba(212,175,55,0.6); background: rgba(40,27,68,0.95); }

    .hw-toast-icon {
      flex-shrink: 0;
      width: 22px;
      height: 22px;
      margin-top: 0.1rem;
    }
    .hw-toast-icon svg { width: 100%; height: 100%; }

    .hw-toast-success .hw-toast-icon { color: #22c55e; }
    .hw-toast-error   .hw-toast-icon { color: #ef4444; }
    .hw-toast-warning .hw-toast-icon { color: #D4AF37; }
    .hw-toast-info    .hw-toast-icon { color: #4f8ef7; }
    .hw-toast-magic   .hw-toast-icon { color: #F5D76E; filter: drop-shadow(0 0 6px #D4AF37); }

    .hw-toast-body { flex: 1; padding-bottom: 1rem; }
    .hw-toast-msg  { font-size: 0.9rem; color: #e2e8f0; font-weight: 500; line-height: 1.5; }

    .hw-toast-close {
      flex-shrink: 0;
      background: none;
      border: none;
      color: #475569;
      cursor: pointer;
      padding: 0.1rem;
      width: 18px;
      height: 18px;
      transition: color 0.2s;
      margin-top: 0.15rem;
    }
    .hw-toast-close:hover { color: #94a3b8; }
    .hw-toast-close svg   { width: 100%; height: 100%; }

    .hw-toast-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: rgba(255,255,255,0.06);
    }
    .hw-toast-progress-bar {
      height: 100%;
      border-radius: 0 0 14px 14px;
      animation: toastCountdown linear forwards;
    }
    .hw-toast-success .hw-toast-progress-bar { background: #22c55e; }
    .hw-toast-error   .hw-toast-progress-bar { background: #ef4444; }
    .hw-toast-warning .hw-toast-progress-bar { background: #D4AF37; }
    .hw-toast-info    .hw-toast-progress-bar { background: #4f8ef7; }
    .hw-toast-magic   .hw-toast-progress-bar { background: linear-gradient(90deg, #D4AF37, #F5D76E); }

    @keyframes toastCountdown {
      from { width: 100%; }
      to   { width: 0%; }
    }

    @media (max-width: 480px) {
      #toast-container {
        bottom: 1rem;
        right: 0.75rem;
        left: 0.75rem;
        max-width: none;
      }
      .hw-toast { min-width: unset; }
    }
  `;
  document.head.appendChild(style);
})();
