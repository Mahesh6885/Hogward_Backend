/**
 * Hogwarts Legacy 5.0 — 24-Hour Magical Countdown Clock Engine
 * Synchronizes with backend PostgreSQL timestamp as the single source of truth.
 * Handles client drift compensation, live per-second ticking, and atmospheric states.
 */

export class HogwartsClock {
  constructor(options = {}) {
    this.container = options.container || document.getElementById('magical-clock-wrap');
    this.digitsEl = options.digitsEl || document.getElementById('clock-digits-val');
    this.statusTagEl = options.statusTagEl || document.getElementById('clock-status-tag');
    this.heroBanner = options.heroBanner || document.getElementById('hero-banner');
    this.onStateChange = options.onStateChange || null;

    this.timerStatus = 'NOT_STARTED'; // NOT_STARTED, RUNNING, PAUSED, COMPLETED
    this.endTime = null;
    this.remainingSeconds = 86400;
    this.clientOffsetMs = 0; // serverTime - clientNow
    this.intervalId = null;
    this.syncIntervalId = null;
    this.celebrated = false;
  }

  async init() {
    await this.syncWithServer();
    this.startLocalTick();

    // Periodic synchronization to prevent drift (every 30 seconds)
    this.syncIntervalId = setInterval(() => this.syncWithServer(), 30000);

    // Immediate resync when browser tab becomes active
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) this.syncWithServer();
    });

    return this;
  }

  async syncWithServer() {
    try {
      const res = await fetch('/api/timer', { cache: 'no-store' });
      const json = await res.json();
      if (json.success && json.data) {
        const d = json.data;
        const serverNow = new Date(d.server_time).getTime();
        const clientNow = Date.now();
        this.clientOffsetMs = serverNow - clientNow;

        this.timerStatus = d.timer_status;
        this.remainingSeconds = d.remaining_seconds;
        this.endTime = d.hackathon_end_time ? new Date(d.hackathon_end_time).getTime() : null;

        this.render();
        if (typeof this.onStateChange === 'function') {
          this.onStateChange(d);
        }
      }
    } catch (e) {
      console.warn('[HogwartsClock] Sync notice:', e);
    }
  }

  startLocalTick() {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = setInterval(() => {
      if (this.timerStatus === 'RUNNING' && this.endTime) {
        const now = Date.now() + this.clientOffsetMs;
        const diffMs = this.endTime - now;
        this.remainingSeconds = Math.max(0, Math.floor(diffMs / 1000));
        if (this.remainingSeconds <= 0) {
          this.timerStatus = 'COMPLETED';
          this.syncWithServer();
        }
      }
      this.render();
    }, 1000);
  }

  render() {
    const s = Math.max(0, this.remainingSeconds);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;

    const formattedTime = `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    const formattedWithSpaces = `${String(hrs).padStart(2, '0')} : ${String(mins).padStart(2, '0')} : ${String(secs).padStart(2, '0')}`;

    // 1. Participant Dashboard live overlay handling
    // When NOT_STARTED: clock image already contains original glowing 24:00:00. Hide overlay to prevent any duplication.
    // When RUNNING/PAUSED/COMPLETED: display visual live countdown inside the clock image container.
    const liveOverlay = this.overlayEl || document.getElementById('clock-live-overlay');
    const liveDigits = this.digitsEl || document.getElementById('clock-live-digits');

    if (liveOverlay) {
      if (this.timerStatus === 'NOT_STARTED') {
        liveOverlay.style.display = 'none';
      } else {
        liveOverlay.style.display = 'flex';
        if (liveDigits) {
          liveDigits.textContent = this.timerStatus === 'COMPLETED' ? '00:00:00' : formattedTime;
        }
      }
    } else if (liveDigits) {
      // Admin dashboard or standalone element
      liveDigits.textContent = this.timerStatus === 'COMPLETED' ? '00 : 00 : 00' : formattedWithSpaces;
    }

    // 2. Status subtitle text
    if (this.statusTagEl) {
      if (this.timerStatus === 'NOT_STARTED') {
        this.statusTagEl.textContent = 'Awaiting Ministry of Magic Signal';
      } else if (this.timerStatus === 'RUNNING') {
        this.statusTagEl.textContent = 'Hackathon In Progress';
      } else if (this.timerStatus === 'PAUSED') {
        this.statusTagEl.textContent = 'Time Frozen by the Ministry';
      } else if (this.timerStatus === 'COMPLETED') {
        this.statusTagEl.textContent = 'Hackathon Completed';
      }
    }

    // 3. Atmospheric Aura classes on clock container and hero banner
    const stateClasses = ['clock-not-started', 'clock-active', 'clock-paused', 'clock-completed'];
    stateClasses.forEach(cls => {
      if (this.container) this.container.classList.remove(cls);
      if (this.heroBanner) this.heroBanner.classList.remove(cls);
    });

    let currentClass = 'clock-not-started';
    if (this.timerStatus === 'RUNNING') currentClass = 'clock-active';
    else if (this.timerStatus === 'PAUSED') currentClass = 'clock-paused';
    else if (this.timerStatus === 'COMPLETED') currentClass = 'clock-completed';

    if (this.container) this.container.classList.add(currentClass);
    if (this.heroBanner) this.heroBanner.classList.add(currentClass);

    // Trigger celebration once upon completion
    if (this.timerStatus === 'COMPLETED' && !this.celebrated) {
      this.celebrated = true;
      this.triggerCelebration();
    }
  }

  triggerCelebration() {
    const celebrationEl = document.getElementById('clock-celebration-ribbon');
    if (celebrationEl) {
      celebrationEl.style.display = 'block';
    }
  }

  destroy() {
    if (this.intervalId) clearInterval(this.intervalId);
    if (this.syncIntervalId) clearInterval(this.syncIntervalId);
  }
}
