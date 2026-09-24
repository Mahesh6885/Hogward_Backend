/**
 * Hogwarts Legacy 5.0 — Magic Wand Cursor & Sparkle Trail
 * Only activates on desktop devices with fine pointer (mouse).
 */

(function () {
  // Check if device uses fine pointer (mouse) and not reduced motion
  if (!window.matchMedia || !window.matchMedia('(pointer: fine)').matches) {
    return;
  }
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // 1. Set Custom Wand Cursor (Golden magic wand with sparkling tip at (2, 2))
  const wandSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
    <defs>
      <linearGradient id="wandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#fff" />
        <stop offset="25%" stop-color="#f8e9a1" />
        <stop offset="55%" stop-color="#d4af37" />
        <stop offset="100%" stop-color="#5c1e1e" />
      </linearGradient>
      <filter id="wandGlow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="1.5" result="glow" />
        <feComposite in="SourceGraphic" in2="glow" operator="over" />
      </filter>
    </defs>
    <!-- Wand shaft -->
    <path d="M3 3 L25 25 L23 27 L1 5 Z" fill="url(#wandGrad)" />
    <!-- Wand core wrapping -->
    <path d="M12 12 L15 15 M16 16 L19 19 M20 20 L23 23" stroke="#f8e9a1" stroke-width="0.75" opacity="0.8" />
    <!-- Wand handle pommel -->
    <circle cx="25" cy="25" r="2.5" fill="#4b1420" stroke="#d4af37" stroke-width="0.8" />
    <!-- Magic tip star sparkle -->
    <polygon points="3,0 4,2 6,3 4,4 3,6 2,4 0,3 2,2" fill="#ffffff" filter="url(#wandGlow)" />
  </svg>`;

  const wandCursorUrl = `url("data:image/svg+xml;utf8,${encodeURIComponent(wandSvg)}") 3 3, auto`;

  const cursorStyle = document.createElement('style');
  cursorStyle.textContent = `
    html, body, button, a, input, select, textarea, .btn, [role="button"] {
      cursor: ${wandCursorUrl} !important;
    }
  `;
  document.head.appendChild(cursorStyle);

  // 2. Create canvas for magic sparkle particles & click ripples
  const canvas = document.createElement('canvas');
  canvas.id = 'magic-cursor-canvas';
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '999999';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const particles = [];
  const ripples = [];
  const colors = [
    '#d4af37', // Gold
    '#f8e9a1', // Antique gold
    '#ffffff', // Lumos white
    '#60a5fa', // Spell blue
    '#facc15', // Spark yellow
  ];

  let lastX = 0;
  let lastY = 0;
  let throttle = 0;

  class Sparkle {
    constructor(x, y, isBurst = false) {
      this.x = x;
      this.y = y;
      const angle = Math.random() * Math.PI * 2;
      const speed = isBurst ? Math.random() * 4.5 + 1.5 : Math.random() * 1.5 + 0.3;
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed - (isBurst ? 0.8 : 0.3); // float up
      this.size = isBurst ? Math.random() * 4 + 2 : Math.random() * 3 + 1.2;
      this.alpha = 1;
      this.decay = isBurst ? Math.random() * 0.035 + 0.015 : Math.random() * 0.03 + 0.02;
      this.color = colors[Math.floor(Math.random() * colors.length)];
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.alpha -= this.decay;
      this.size *= 0.96;
    }

    draw(ctx) {
      ctx.save();
      ctx.globalAlpha = Math.max(0, this.alpha);
      ctx.fillStyle = this.color;
      ctx.shadowBlur = 8;
      ctx.shadowColor = this.color;

      // Draw a 4-point magical star spark
      ctx.beginPath();
      const s = this.size;
      ctx.moveTo(this.x, this.y - s);
      ctx.quadraticCurveTo(this.x, this.y, this.x + s, this.y);
      ctx.quadraticCurveTo(this.x, this.y, this.x, this.y + s);
      ctx.quadraticCurveTo(this.x, this.y, this.x - s, this.y);
      ctx.quadraticCurveTo(this.x, this.y, this.x, this.y - s);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  class MagicalRipple {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.radius = 4;
      this.maxRadius = 36;
      this.alpha = 0.9;
    }

    update() {
      this.radius += 2.2;
      this.alpha -= 0.055;
    }

    draw(ctx) {
      if (this.alpha <= 0) return;
      ctx.save();
      ctx.globalAlpha = Math.max(0, this.alpha);
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.strokeStyle = '#f8e9a1';
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 10;
      ctx.shadowColor = '#d4af37';
      ctx.stroke();

      // Inner faint ring
      if (this.radius > 10) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius * 0.6, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(212,175,55,0.4)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  // Mouse move sparkle trail
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX;
    const y = e.clientY;
    const dist = Math.hypot(x - lastX, y - lastY);

    if (dist > 4 && ++throttle % 2 === 0) {
      const count = Math.min(3, Math.floor(dist / 12) + 1);
      for (let i = 0; i < count; i++) {
        particles.push(new Sparkle(x + (Math.random() - 0.5) * 5, y + (Math.random() - 0.5) * 5));
      }
      lastX = x;
      lastY = y;
    }
  }, { passive: true });

  // Mouse click: Magical Ripple + Golden Particle Burst
  document.addEventListener('click', (e) => {
    const x = e.clientX;
    const y = e.clientY;

    // 1. Expanding ripple
    ripples.push(new MagicalRipple(x, y));

    // 2. Spell particle burst
    for (let i = 0; i < 18; i++) {
      particles.push(new Sparkle(x, y, true));
    }
  }, { passive: true });

  function render() {
    ctx.clearRect(0, 0, width, height);

    // Render & update ripples
    for (let i = ripples.length - 1; i >= 0; i--) {
      const r = ripples[i];
      r.update();
      if (r.alpha <= 0) {
        ripples.splice(i, 1);
      } else {
        r.draw(ctx);
      }
    }

    // Render & update sparkles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.update();
      if (p.alpha <= 0.02 || p.size <= 0.2) {
        particles.splice(i, 1);
      } else {
        p.draw(ctx);
      }
    }

    requestAnimationFrame(render);
  }

  render();
})();
