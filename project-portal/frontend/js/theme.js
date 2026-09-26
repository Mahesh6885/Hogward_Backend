/**
 * HOGWARTS LEGACY 5.0 — Theme Utilities
 * - Magical full-screen loader
 * - Countdown timer widget
 * - Animated stat counters
 * - Skeleton loading
 * - Success animation (golden sparks)
 */

// ── Web Audio API Synthesizer (Magical Sound Effects, Zero-Asset) ──────────────
let audioCtx = null;
let soundMuted = false;

function getAudioContext() {
  if (!audioCtx && (window.AudioContext || window.webkitAudioContext)) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

export function toggleThemeSound() {
  soundMuted = !soundMuted;
  localStorage.setItem('hw_sound_muted', soundMuted ? '1' : '0');
  return !soundMuted;
}

export function isThemeSoundMuted() {
  return soundMuted || localStorage.getItem('hw_sound_muted') === '1';
}

export function playMagicalSound(type = 'chime') {
  if (isThemeSoundMuted()) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    if (type === 'chime' || type === 'spell') {
      // Golden magical chime chords
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08);

        gain.gain.setValueAtTime(0.001, ctx.currentTime + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + idx * 0.08 + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + idx * 0.08 + 0.6);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + idx * 0.08);
        osc.stop(ctx.currentTime + idx * 0.08 + 0.65);
      });
    } else if (type === 'fanfare') {
      // Hogwarts Great Hall triumphant fanfare
      const melody = [
        { f: 440.00, t: 0.0,  d: 0.25 }, // A4
        { f: 554.37, t: 0.25, d: 0.25 }, // C#5
        { f: 659.25, t: 0.50, d: 0.40 }, // E5
        { f: 880.00, t: 0.90, d: 0.80 }, // A5
      ];
      melody.forEach(item => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(item.f, ctx.currentTime + item.t);

        gain.gain.setValueAtTime(0.001, ctx.currentTime + item.t);
        gain.gain.linearRampToValueAtTime(0.15, ctx.currentTime + item.t + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + item.t + item.d);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + item.t);
        osc.stop(ctx.currentTime + item.t + item.d + 0.05);
      });
    } else if (type === 'snitch') {
      // Golden Snitch flutter chime
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(987.77, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1318.51, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.26);
    }
  } catch (err) {
    // Audio contexts safely handled
  }
}

// ── Magical Full-Screen & Creature Loaders ──────────────────────────────────
let loaderEl = null;

export function showCinematicLoader(domainOrRole = 'AI', customMsg = '') {
  if (document.getElementById('hw-loader')) return;

  const key = String(domainOrRole || 'AI').toUpperCase();
  let creatureSvg = '';
  let creatureText = customMsg;
  let accentColor = '#D4AF37';

  if (key === 'AI' || key === 'GRYFFINDOR') {
    accentColor = '#D4AF37';
    creatureText = customMsg || 'The Phoenix is awakening your AI Realm.';
    creatureSvg = `
      <div class="creature-phoenix-wrap">
        <svg viewBox="0 0 100 100" class="creature-svg phoenix-svg">
          <path d="M50 15 C45 30 20 40 10 55 C25 55 40 45 45 60 C35 70 20 75 15 90 C30 85 45 75 50 85 C55 75 70 85 85 90 C80 75 65 70 55 60 C60 45 75 55 90 55 C80 40 55 30 50 15 Z" fill="url(#phoenixGrad)" filter="url(#fireGlow)" />
          <circle cx="50" cy="20" r="4" fill="#FFE57F" />
          <defs>
            <linearGradient id="phoenixGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#FFF275" />
              <stop offset="30%" stop-color="#FF8C00" />
              <stop offset="70%" stop-color="#D4AF37" />
              <stop offset="100%" stop-color="#740001" />
            </linearGradient>
            <filter id="fireGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="glow" />
              <feComposite in="SourceGraphic" in2="glow" operator="over" />
            </filter>
          </defs>
        </svg>
        <div class="feather-particles">
          <span style="left:20%;animation-delay:0s">🪶</span>
          <span style="left:50%;animation-delay:0.4s">✨</span>
          <span style="left:75%;animation-delay:0.8s">🔥</span>
        </div>
      </div>
    `;
  } else if (key === 'CYBERSECURITY' || key === 'SLYTHERIN') {
    accentColor = '#2AA146';
    creatureText = customMsg || 'The Basilisk is securing your vault.';
    creatureSvg = `
      <div class="creature-basilisk-wrap">
        <div class="basilisk-eye">
          <div class="basilisk-iris"></div>
          <div class="basilisk-pupil"></div>
        </div>
        <div class="security-glyphs">
          <span>01</span><span>🛡️</span><span>KEY</span><span>⚡</span>
        </div>
      </div>
    `;
  } else if (key === 'OPEN_INNOVATION' || key === 'RAVENCLAW' || key === 'OPEN INNOVATION') {
    accentColor = '#60A5FA';
    creatureText = customMsg || 'The Raven delivers ancient knowledge.';
    creatureSvg = `
      <div class="creature-raven-wrap">
        <svg viewBox="0 0 100 100" class="creature-svg raven-svg">
          <path d="M50 20 C40 30 15 45 5 60 C25 60 40 45 45 65 C35 75 25 80 20 92 C35 85 45 75 50 82 C55 75 65 85 80 92 C75 80 65 75 55 65 C60 45 75 60 95 60 C85 45 60 30 50 20 Z" fill="url(#ravenGrad)" filter="url(#ravenGlow)" />
          <rect x="42" y="70" width="16" height="8" rx="2" fill="#F7F0D5" stroke="#D4AF37" stroke-width="1" transform="rotate(-10 50 74)"/>
          <defs>
            <linearGradient id="ravenGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#93C5FD" />
              <stop offset="50%" stop-color="#2563EB" />
              <stop offset="100%" stop-color="#0E1A40" />
            </linearGradient>
            <filter id="ravenGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="glow" />
              <feComposite in="SourceGraphic" in2="glow" operator="over" />
            </filter>
          </defs>
        </svg>
        <div class="feather-particles blue">
          <span style="left:25%;animation-delay:0.1s">🪶</span>
          <span style="left:70%;animation-delay:0.5s">📜</span>
        </div>
      </div>
    `;
  } else {
    // Admin / Chief Arbiter Patronus
    accentColor = '#E0E7FF';
    creatureText = customMsg || 'The Ministry of Magic is preparing the Review Chamber.';
    creatureSvg = `
      <div class="creature-patronus-wrap">
        <div class="patronus-orb">
          <div class="patronus-inner">🦌</div>
        </div>
        <div class="patronus-mist"></div>
      </div>
    `;
  }

  loaderEl = document.createElement('div');
  loaderEl.id = 'hw-loader';
  loaderEl.className = `cinematic-loader realm-${key.toLowerCase()}`;
  loaderEl.innerHTML = `
    <div class="hw-loader-inner">
      ${creatureSvg}
      <div class="hw-loader-brand" style="color:${accentColor}">HOGWARTS LEGACY 5.0</div>
      <div class="hw-loader-msg" id="hw-loader-msg">${creatureText}</div>
      <div class="hw-loader-dots">
        <span style="background:${accentColor}"></span>
        <span style="background:${accentColor}"></span>
        <span style="background:${accentColor}"></span>
      </div>
    </div>
  `;
  document.body.appendChild(loaderEl);
  requestAnimationFrame(() => loaderEl.classList.add('hw-loader-visible'));
  playMagicalSound('spell');
}

export function showLoader(message = 'Summoning the Magic…', domainOrRole = null) {
  if (domainOrRole) {
    showCinematicLoader(domainOrRole, message);
    return;
  }
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

// ── Time Turner Gyroscopic Countdown Widget ──────────────────────────────────
export function initTimeTurner(containerId, targetDate = HACKATHON_DATE) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.className = 'time-turner-container';

  function update() {
    const now  = Date.now();
    const diff = targetDate.getTime() - now;

    if (diff <= 0) {
      container.innerHTML = `
        <div class="time-turner-rings">
          <div class="time-turner-ring"></div>
          <div class="time-turner-ring inner"></div>
          <div class="time-turner-ring core"></div>
        </div>
        <div class="hw-countdown-started" style="font-family:'Cinzel',serif;color:#D4AF37;font-size:1.1rem">
          🔥 The 24-Hour Hourglass has Turned! Hackathon Live!
        </div>
      `;
      return;
    }

    const days  = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const mins  = Math.floor((diff % 3600000)  / 60000);
    const secs  = Math.floor((diff % 60000)    / 1000);

    container.innerHTML = `
      <div class="time-turner-rings" title="Time Turner Gyroscope">
        <div class="time-turner-ring"></div>
        <div class="time-turner-ring inner"></div>
        <div class="time-turner-ring core"></div>
      </div>
      <div class="time-turner-timer">
        <div class="turner-unit">
          <div class="turner-val">${String(days).padStart(2, '0')}</div>
          <div class="turner-label">Days</div>
        </div>
        <div class="turner-sep">:</div>
        <div class="turner-unit">
          <div class="turner-val">${String(hours).padStart(2, '0')}</div>
          <div class="turner-label">Hours</div>
        </div>
        <div class="turner-sep">:</div>
        <div class="turner-unit">
          <div class="turner-val">${String(mins).padStart(2, '0')}</div>
          <div class="turner-label">Mins</div>
        </div>
        <div class="turner-sep">:</div>
        <div class="turner-unit">
          <div class="turner-val">${String(secs).padStart(2, '0')}</div>
          <div class="turner-label">Secs</div>
        </div>
      </div>
    `;
  }

  update();
  return setInterval(update, 1000);
}

// ── Sorting Hat Ceremony (First Login Cinematic Experience) ─────────────────
export function runSortingCeremony({ teamName, domainName, onComplete }) {
  if (document.getElementById('ceremony-modal-root')) return;

  const houseMap = {
    'AI': { name: 'GRYFFINDOR', class: 'gryffindor', emblem: '🦁', color: '#D4AF37', trait: 'Daring, nerve, and chivalry.' },
    'CYBERSECURITY': { name: 'SLYTHERIN', class: 'slytherin', emblem: '🐍', color: '#2AA146', trait: 'Resourcefulness, ambition, and cunning.' },
    'OPEN_INNOVATION': { name: 'RAVENCLAW', class: 'ravenclaw', emblem: '🦅', color: '#60A5FA', trait: 'Wisdom, wit, and unbounded creativity.' },
    'OPEN INNOVATION': { name: 'RAVENCLAW', class: 'ravenclaw', emblem: '🦅', color: '#60A5FA', trait: 'Wisdom, wit, and unbounded creativity.' },
  };

  const domainKey = String(domainName || 'AI').toUpperCase().replace(' ', '_');
  const house = houseMap[domainKey] || houseMap['AI'];

  const modal = document.createElement('div');
  modal.id = 'ceremony-modal-root';
  modal.className = 'ceremony-modal active';
  modal.innerHTML = `
    <div class="ceremony-doors-wrap" id="ceremony-doors">
      <div class="ceremony-door left"><div class="ceremony-door-handle">🏰</div></div>
      <div class="ceremony-door right"><div class="ceremony-door-handle">⚡</div></div>
    </div>
    <button class="ceremony-mute-btn" id="ceremony-mute-toggle" title="Toggle Sound">
      ${isThemeSoundMuted() ? '🔇 Unmute' : '🔊 Sound On'}
    </button>
    <div class="ceremony-stage">
      <div class="ceremony-hat-icon">🧙‍♂️</div>
      <h2 style="font-family:'Cinzel',serif;color:#D4AF37;letter-spacing:0.15em;margin-bottom:0.5rem">
        THE GREAT HALL CEREMONY
      </h2>
      <div class="ceremony-dialogue" id="ceremony-text">
        "Welcome to Hogwarts Legacy 5.0... Step forward, ${teamName}!"
      </div>
      <div class="ceremony-house-result ${house.class}" id="ceremony-house-badge">
        ${house.name}!
      </div>
      <div class="ceremony-banner-unfurl ${house.class}" id="ceremony-banner">
        <span>${house.emblem}</span>
      </div>
      <div class="ceremony-actions">
        <button class="ceremony-skip-btn" id="ceremony-skip-btn" style="opacity:0;transition:opacity 0.4s ease">
          Skip Ceremony →
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Mute toggle inside ceremony
  const muteBtn = modal.querySelector('#ceremony-mute-toggle');
  muteBtn.addEventListener('click', () => {
    const unmuted = toggleThemeSound();
    muteBtn.textContent = unmuted ? '🔊 Sound On' : '🔇 Unmute';
  });

  const doors = modal.querySelector('#ceremony-doors');
  const dialogue = modal.querySelector('#ceremony-text');
  const houseBadge = modal.querySelector('#ceremony-house-badge');
  const banner = modal.querySelector('#ceremony-banner');
  const skipBtn = modal.querySelector('#ceremony-skip-btn');

  let finished = false;
  function finish() {
    if (finished) return;
    finished = true;
    modal.classList.remove('active');
    setTimeout(() => {
      modal.remove();
      if (typeof onComplete === 'function') onComplete();
    }, 600);
  }

  skipBtn.addEventListener('click', finish);

  // Enable skip button after 3 seconds as required
  setTimeout(() => {
    skipBtn.style.opacity = '1';
  }, 3000);

  // Sequence:
  // Step 1: Open Great Hall Oak Doors
  setTimeout(() => {
    doors.classList.add('doors-opened');
    playMagicalSound('chime');
  }, 800);

  // Step 2: Sorting Hat ponders
  setTimeout(() => {
    dialogue.textContent = `"Hmm... Let's see... ${teamName}... A keen mind suited for ${domainName || 'Hackathon Realm'}!"`;
    playMagicalSound('spell');
  }, 2200);

  // Step 3: Proclamation of House
  setTimeout(() => {
    dialogue.textContent = `"There is no doubt in my mind... You belong in..."`;
  }, 4400);

  // Step 4: Hat proclaims House!
  setTimeout(() => {
    dialogue.textContent = `"${house.name}! Where dwell the brave and creative!"`;
    houseBadge.classList.add('revealed');
    banner.classList.add('unfurled');
    playMagicalSound('fanfare');
  }, 6200);

  // Step 5: Transition to dashboard
  setTimeout(() => {
    finish();
  }, 9500);
}

// ── Project Submission Owl Animation ─────────────────────────────────────────
export function showProjectSubmissionOwl(onDone) {
  const overlay = document.createElement('div');
  overlay.className = 'hw-loader-overlay';
  overlay.style.position = 'fixed';
  overlay.style.inset = '0';
  overlay.style.zIndex = '999998';
  overlay.style.background = 'radial-gradient(ellipse at 50% 50%, #091229 0%, #050505 100%)';
  overlay.style.display = 'flex';
  overlay.style.flexDirection = 'column';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.padding = '2rem';
  overlay.style.textAlign = 'center';

  overlay.innerHTML = `
    <div style="font-size:5rem;animation:castleFloat 2.5s ease-in-out infinite">🦉</div>
    <div style="font-size:2rem;margin-top:0.5rem">📜✨</div>
    <h2 style="font-family:'Cinzel',serif;color:#D4AF37;margin:1rem 0 0.5rem;font-size:1.75rem">
      SPELL DELIVERED!
    </h2>
    <p style="font-family:'Cormorant Garamond',serif;font-size:1.35rem;font-style:italic;color:#F7F0D5;max-width:500px">
      "Your project scroll has been carried by the Owl Post to the Ministry of Magic Evaluation Chamber."
    </p>
    <div class="hw-loader-dots" style="margin-top:1.5rem">
      <span></span><span></span><span></span>
    </div>
  `;
  document.body.appendChild(overlay);
  playMagicalSound('spell');

  setTimeout(() => {
    overlay.style.transition = 'opacity 0.6s ease';
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.remove();
      if (typeof onDone === 'function') onDone();
    }, 600);
  }, 3200);
}

// ── Golden Snitch Easter Egg ─────────────────────────────────────────────────
export function initGoldenSnitch() {
  if (document.getElementById('golden-snitch-egg')) return;

  function spawnSnitch() {
    if (document.getElementById('golden-snitch-egg')) return;
    const snitch = document.createElement('div');
    snitch.id = 'golden-snitch-egg';
    snitch.className = 'golden-snitch';
    snitch.title = 'Catch the Golden Snitch!';

    let posX = Math.random() * (window.innerWidth - 60) + 30;
    let posY = Math.random() * (window.innerHeight - 100) + 50;
    snitch.style.left = `${posX}px`;
    snitch.style.top = `${posY}px`;

    document.body.appendChild(snitch);

    let moveInterval = setInterval(() => {
      if (!snitch.parentNode) {
        clearInterval(moveInterval);
        return;
      }
      posX += (Math.random() - 0.5) * 160;
      posY += (Math.random() - 0.5) * 120;
      posX = Math.max(30, Math.min(window.innerWidth - 60, posX));
      posY = Math.max(60, Math.min(window.innerHeight - 80, posY));
      snitch.style.transform = `translate(${posX}px, ${posY}px)`;
    }, 900);

    snitch.addEventListener('click', (e) => {
      e.stopPropagation();
      clearInterval(moveInterval);
      playMagicalSound('snitch');
      import('./toast.js').then(({ toast }) => {
        toast.magic('🏆 +50 Points to your House! You caught the Golden Snitch!');
      });
      snitch.style.transform = `translate(${posX}px, ${posY}px) scale(2)`;
      snitch.style.opacity = '0';
      setTimeout(() => snitch.remove(), 400);
    });

    // Auto-fly away after 14 seconds
    setTimeout(() => {
      if (snitch.parentNode) {
        clearInterval(moveInterval);
        snitch.style.transition = 'all 1s ease-in';
        snitch.style.transform = `translate(${window.innerWidth + 100}px, -100px)`;
        setTimeout(() => snitch.remove(), 1000);
      }
    }, 14000);
  }

  // First spawn after 25s, then occasionally every 90-180s
  setTimeout(spawnSnitch, 25000);
  setInterval(spawnSnitch, 120000);
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
