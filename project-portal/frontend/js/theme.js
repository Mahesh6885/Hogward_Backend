/**
 * HOGWARTS LEGACY 5.0 — Theme Utilities
 * - Magical full-screen loader
 * - Countdown timer widget
 * - Animated stat counters
 * - Skeleton loading
 * - Success animation (golden sparks)
 */

// ── Magical Full-Screen Loader ───────────────────────────────────────────────
let loaderEl = null;

export function showLoader(message = 'Summoning the Magic…') {
  if (document.getElementById('hw-loader')) return;

  loaderEl = document.createElement('div');
  loaderEl.id = 'hw-loader';
  loaderEl.innerHTML = `
    <div class="hw-loader-inner">
      <div class="hw-loader-crest">
        <div class="hw-spell-ring hw-spell-ring-1"></div>
        <div class="hw-spell-ring hw-spell-ring-2"></div>
        <div class="hw-spell-ring hw-spell-ring-3"></div>
        <div class="hw-loader-symbol">⚡</div>
      </div>
      <div class="hw-loader-brand">HOGWARTS LEGACY</div>
      <div class="hw-loader-sub">5.0</div>
      <div class="hw-loader-msg" id="hw-loader-msg">${message}</div>
      <div class="hw-loader-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  document.body.appendChild(loaderEl);
  requestAnimationFrame(() => loaderEl.classList.add('hw-loader-visible'));
}

export function hideLoader(delay = 400) {
  const el = document.getElementById('hw-loader');
  if (!el) return;
  setTimeout(() => {
    el.classList.add('hw-loader-fade-out');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
  }, delay);
}

export function updateLoaderMessage(msg) {
  const el = document.getElementById('hw-loader-msg');
  if (el) el.textContent = msg;
}

// ── Countdown Timer ──────────────────────────────────────────────────────────
// Default hackathon date — change this to actual date!
export const HACKATHON_DATE = new Date('2025-10-25T09:00:00+05:30');

export function initCountdown(containerId, targetDate = HACKATHON_DATE) {
  const container = document.getElementById(containerId);
  if (!container) return;

  function update() {
    const now  = Date.now();
    const diff = targetDate.getTime() - now;

    if (diff <= 0) {
      container.innerHTML = `
        <div class="hw-countdown-started">
          <span class="hw-countdown-fire">🔥</span>
          <span>Hackathon Has Begun!</span>
          <span class="hw-countdown-fire">🔥</span>
        </div>`;
      return;
    }

    const days  = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const mins  = Math.floor((diff % 3600000)  / 60000);
    const secs  = Math.floor((diff % 60000)    / 1000);

    container.innerHTML = `
      <div class="hw-countdown-grid">
        ${unit(days,  'Days')}
        <div class="hw-countdown-colon">:</div>
        ${unit(hours, 'Hours')}
        <div class="hw-countdown-colon">:</div>
        ${unit(mins,  'Mins')}
        <div class="hw-countdown-colon">:</div>
        ${unit(secs,  'Secs')}
      </div>
    `;
  }

  function unit(val, label) {
    return `
      <div class="hw-countdown-unit">
        <div class="hw-countdown-val">${String(val).padStart(2, '0')}</div>
        <div class="hw-countdown-label">${label}</div>
      </div>
    `;
  }

  update();
  return setInterval(update, 1000);
}

// ── Animated Counters ────────────────────────────────────────────────────────
export function animateCounter(el, target, duration = 1200) {
  if (!el) return;
  const start     = performance.now();
  const startVal  = 0;
  const endVal    = parseInt(target, 10) || 0;

  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const current  = Math.round(startVal + (endVal - startVal) * easeOut(progress));
    el.textContent = current;
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = endVal;
  }
  requestAnimationFrame(step);
}

export function animateAllCounters(selector = '[data-counter]') {
  const els = document.querySelectorAll(selector);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target, entry.target.dataset.counter);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });
  els.forEach(el => observer.observe(el));
}

// ── Skeleton Loading ─────────────────────────────────────────────────────────
export function createSkeleton(lines = 3) {
  return `
    <div class="hw-skeleton-card">
      ${Array.from({ length: lines }, (_, i) => `
        <div class="hw-skeleton-line" style="width:${i === 0 ? '60%' : i % 2 === 0 ? '80%' : '100%'}"></div>
      `).join('')}
    </div>
  `;
}

export function showSkeletons(containerId, count = 4) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array.from({ length: count }, () => createSkeleton(3)).join('');
}

// ── Success Animation (Golden Sparks) ────────────────────────────────────────
export function showSuccessAnimation(message = 'Project Submitted Successfully!') {
  const overlay = document.createElement('div');
  overlay.className = 'hw-success-overlay';
  overlay.innerHTML = `
    <div class="hw-success-box">
      <canvas id="hw-success-canvas"></canvas>
      <div class="hw-success-icon">✨</div>
      <h2 class="hw-success-title">Success!</h2>
      <p class="hw-success-msg">${message}</p>
      <button class="btn btn-primary hw-success-close" onclick="this.closest('.hw-success-overlay').remove()">
        Continue →
      </button>
    </div>
  `;
  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('hw-success-visible'));

  // Run spark particle burst
  const canvas = document.getElementById('hw-success-canvas');
  runSparkBurst(canvas);

  // Auto-dismiss after 5s
  setTimeout(() => {
    overlay.classList.add('hw-success-exit');
    overlay.addEventListener('transitionend', () => overlay.remove(), { once: true });
  }, 5000);
}

function runSparkBurst(canvas) {
  if (!canvas) return;
  const W = canvas.width  = canvas.offsetWidth  || 400;
  const H = canvas.height = canvas.offsetHeight || 300;
  const ctx = canvas.getContext('2d');

  const sparks = Array.from({ length: 80 }, () => ({
    x: W / 2, y: H / 2,
    vx: (Math.random() - 0.5) * 12,
    vy: (Math.random() - 0.5) * 12,
    r:  Math.random() * 4 + 1,
    a:  1,
    color: ['#D4AF37', '#F5D76E', '#fff', '#fbbf24', '#D4AF37'][Math.floor(Math.random() * 5)],
  }));

  let frame = 0;
  function draw() {
    ctx.clearRect(0, 0, W, H);
    sparks.forEach(s => {
      s.x  += s.vx;
      s.y  += s.vy;
      s.vy += 0.2;  // gravity
      s.a  -= 0.02;
      if (s.a <= 0) return;
      ctx.save();
      ctx.globalAlpha = s.a;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = s.color;
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#D4AF37';
      ctx.fill();
      ctx.restore();
    });
    if (++frame < 120) requestAnimationFrame(draw);
  }
  draw();
}

// ── Inject Theme Utility Styles ──────────────────────────────────────────────
(function injectThemeStyles() {
  if (document.getElementById('hw-theme-util-styles')) return;
  const style = document.createElement('style');
  style.id = 'hw-theme-util-styles';
  style.textContent = `
    /* ── Loader ── */
    #hw-loader {
      position: fixed; inset: 0; z-index: 99998;
      background: radial-gradient(ellipse at 50% 60%, #0F172A 0%, #080808 100%);
      display: flex; align-items: center; justify-content: center;
      opacity: 0; transition: opacity 0.4s ease;
    }
    #hw-loader.hw-loader-visible  { opacity: 1; }
    #hw-loader.hw-loader-fade-out { opacity: 0; }

    .hw-loader-inner {
      text-align: center; display: flex; flex-direction: column; align-items: center; gap: 0.75rem;
    }
    .hw-loader-crest {
      position: relative; width: 100px; height: 100px;
      display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;
    }
    .hw-spell-ring {
      position: absolute; border-radius: 50%; border: 2px solid transparent;
      animation: spellRotate linear infinite;
    }
    .hw-spell-ring-1 { width: 100px; height: 100px; border-top-color: #D4AF37; border-right-color: rgba(212,175,55,0.3); animation-duration: 1.2s; }
    .hw-spell-ring-2 { width: 75px;  height: 75px;  border-bottom-color: #F5D76E; border-left-color: rgba(245,215,110,0.3); animation-duration: 1.8s; animation-direction: reverse; }
    .hw-spell-ring-3 { width: 50px;  height: 50px;  border-top-color: rgba(212,175,55,0.6); animation-duration: 2.4s; }
    @keyframes spellRotate { to { transform: rotate(360deg); } }

    .hw-loader-symbol {
      font-size: 1.75rem; z-index: 1;
      animation: loaderPulse 1.5s ease-in-out infinite;
    }
    @keyframes loaderPulse { 0%,100%{transform:scale(1);} 50%{transform:scale(1.15);} }

    .hw-loader-brand {
      font-family: 'Cinzel', 'Georgia', serif; font-size: 1.5rem; font-weight: 700;
      color: #D4AF37; letter-spacing: 0.2em;
      text-shadow: 0 0 20px rgba(212,175,55,0.5);
    }
    .hw-loader-sub {
      font-family: 'Cinzel', serif; font-size: 1rem; color: rgba(212,175,55,0.7);
      letter-spacing: 0.4em; margin-top: -0.5rem;
    }
    .hw-loader-msg { font-size: 0.875rem; color: #94a3b8; letter-spacing: 0.05em; }
    .hw-loader-dots { display: flex; gap: 0.4rem; margin-top: 0.25rem; }
    .hw-loader-dots span {
      width: 6px; height: 6px; border-radius: 50%; background: #D4AF37;
      animation: dotBounce 1.2s ease-in-out infinite;
    }
    .hw-loader-dots span:nth-child(2) { animation-delay: 0.2s; }
    .hw-loader-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotBounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4;} 40%{transform:scale(1);opacity:1;} }

    /* ── Countdown ── */
    .hw-countdown-grid {
      display: flex; align-items: center; gap: 0.5rem; justify-content: center; flex-wrap: wrap;
    }
    .hw-countdown-unit { text-align: center; }
    .hw-countdown-val {
      font-family: 'Cinzel', monospace; font-size: 2rem; font-weight: 700;
      color: #D4AF37; background: rgba(212,175,55,0.1);
      border: 1px solid rgba(212,175,55,0.3);
      border-radius: 8px; padding: 0.4rem 0.75rem;
      min-width: 64px;
      text-shadow: 0 0 10px rgba(212,175,55,0.5);
    }
    .hw-countdown-label { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.25rem; }
    .hw-countdown-colon { font-size: 2rem; font-weight: 700; color: rgba(212,175,55,0.5); margin-bottom: 1.25rem; }
    .hw-countdown-started { display: flex; align-items: center; gap: 0.75rem; font-family: 'Cinzel',serif; font-size: 1.1rem; color: #D4AF37; }
    .hw-countdown-fire { font-size: 1.5rem; animation: loaderPulse 1s infinite; }

    /* ── Skeleton ── */
    .hw-skeleton-card { padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; }
    .hw-skeleton-line {
      height: 14px; border-radius: 7px;
      background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%);
      background-size: 200% 100%;
      animation: skeletonShimmer 1.5s infinite;
    }
    @keyframes skeletonShimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

    /* ── Success overlay ── */
    .hw-success-overlay {
      position: fixed; inset: 0; z-index: 99997;
      background: rgba(8,8,8,0.85); backdrop-filter: blur(8px);
      display: flex; align-items: center; justify-content: center;
      opacity: 0; transition: opacity 0.4s ease;
    }
    .hw-success-overlay.hw-success-visible { opacity: 1; }
    .hw-success-overlay.hw-success-exit    { opacity: 0; }
    .hw-success-box {
      position: relative; text-align: center; padding: 3rem 2.5rem;
      background: rgba(15,23,42,0.95); border: 1px solid rgba(212,175,55,0.4);
      border-radius: 20px; max-width: 420px; width: calc(100% - 3rem);
    }
    #hw-success-canvas {
      position: absolute; top: 0; left: 0; width: 100%; height: 100%;
      pointer-events: none; border-radius: 20px;
    }
    .hw-success-icon { font-size: 3.5rem; animation: loaderPulse 1s infinite; }
    .hw-success-title {
      font-family: 'Cinzel', serif; font-size: 1.75rem; color: #D4AF37;
      margin: 0.75rem 0 0.5rem;
    }
    .hw-success-msg   { font-size: 1rem; color: #94a3b8; margin-bottom: 1.5rem; }
    .hw-success-close { position: relative; z-index: 1; }

    /* ── Session Timeout Modal ── */
    .hw-session-modal {
      position: fixed; inset: 0; z-index: 99996;
      background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
      display: flex; align-items: center; justify-content: center;
      padding: 1rem;
    }
    .hw-session-modal.hidden { display: none; }
    .hw-session-modal-box {
      background: rgba(15,23,42,0.97); border: 1px solid rgba(212,175,55,0.4);
      border-radius: 16px; padding: 2.5rem 2rem; text-align: center; max-width: 400px; width: 100%;
      box-shadow: 0 0 60px rgba(212,175,55,0.15);
    }
    .hw-session-modal-icon  { font-size: 3rem; margin-bottom: 1rem; animation: loaderPulse 1.5s infinite; }
    .hw-session-modal-title { font-family: 'Cinzel', serif; color: #D4AF37; margin-bottom: 0.75rem; font-size: 1.5rem; }
    .hw-session-modal-body  { color: #94a3b8; margin-bottom: 1.5rem; font-size: 0.95rem; }
    .hw-session-modal-body strong { color: #D4AF37; }
    .hw-session-modal-actions { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }

    /* ── Password Strength ── */
    .pw-strength-bar-wrap {
      height: 5px; background: rgba(255,255,255,0.1); border-radius: 3px; margin-bottom: 0.5rem; overflow: hidden;
    }
    .pw-strength-bar-fill {
      height: 100%; border-radius: 3px; transition: width 0.4s ease, background 0.4s ease;
    }
    .pw-strength-meta { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
    .pw-strength-label { font-size: 0.75rem; font-weight: 700; }
    .pw-strength-checks { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .pw-check {
      font-size: 0.68rem; color: #475569; transition: color 0.2s;
      background: rgba(255,255,255,0.04); padding: 0.15rem 0.4rem; border-radius: 4px;
    }
    .pw-check.ok { color: #22c55e; }

    /* ── Spinner ── */
    .hw-spinner {
      display: inline-block; width: 16px; height: 16px;
      border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
      border-radius: 50%; animation: spellRotate 0.7s linear infinite;
      margin-right: 0.4rem; vertical-align: middle;
    }
  `;
  document.head.appendChild(style);
})();
