/**
 * HOGWARTS LEGACY 5.0 — Magical Floating Particles
 * Lightweight canvas-based gold particle system.
 */

export function initParticles(options = {}) {
  const {
    count = window.innerWidth < 768 ? 30 : 60,
    color = '#D4AF37',
    opacity = 0.6,
    speed = 0.4,
    size = { min: 1, max: 3 },
  } = options;

  const canvas = document.createElement('canvas');
  canvas.id = 'particles-canvas';
  canvas.style.cssText = `
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
    opacity: 0.7;
  `;
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d');
  let W = 0, H = 0;
  let particles = [];
  let animId;
  let paused = false;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function hexToRgb(hex) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return `${r},${g},${b}`;
  }

  const rgb = hexToRgb(color);

  class Particle {
    constructor() { this.reset(true); }

    reset(init = false) {
      this.x    = Math.random() * W;
      this.y    = init ? Math.random() * H : H + 10;
      this.vx   = (Math.random() - 0.5) * speed;
      this.vy   = -(Math.random() * speed + 0.1);
      this.r    = Math.random() * (size.max - size.min) + size.min;
      this.a    = Math.random() * opacity;
      this.da   = (Math.random() - 0.5) * 0.005;
      this.life = 0;
      this.maxLife = Math.random() * 200 + 100;
      // Occasional sparkle
      this.sparkle = Math.random() < 0.15;
      this.sparkleAngle = 0;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.a += this.da;
      this.life++;
      this.sparkleAngle += 0.05;

      if (this.a <= 0) this.da *= -1;
      if (this.a > opacity) this.da *= -1;
      if (this.life > this.maxLife || this.y < -10) this.reset();
    }

    draw() {
      ctx.save();
      if (this.sparkle) {
        // Draw small star shape
        ctx.translate(this.x, this.y);
        ctx.rotate(this.sparkleAngle);
        ctx.globalAlpha = this.a;
        ctx.fillStyle = `rgba(${rgb},1)`;
        drawStar(ctx, 0, 0, this.r * 2.5, this.r * 1, 4);
        ctx.fill();
      } else {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.globalAlpha = this.a;
        ctx.fillStyle = `rgba(${rgb},1)`;
        ctx.shadowBlur = 6;
        ctx.shadowColor = `rgba(${rgb},0.8)`;
        ctx.fill();
      }
      ctx.restore();
    }
  }

  function drawStar(ctx, cx, cy, outerR, innerR, points) {
    ctx.beginPath();
    for (let i = 0; i < points * 2; i++) {
      const r = i % 2 === 0 ? outerR : innerR;
      const angle = (Math.PI / points) * i - Math.PI / 2;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
  }

  function init() {
    resize();
    particles = Array.from({ length: count }, () => new Particle());
  }

  function animate() {
    if (paused) return;
    ctx.clearRect(0, 0, W, H);
    for (const p of particles) {
      p.update();
      p.draw();
    }
    animId = requestAnimationFrame(animate);
  }

  window.addEventListener('resize', () => {
    resize();
    // Re-clamp positions
    for (const p of particles) {
      if (p.x > W) p.x = Math.random() * W;
    }
  });

  // Pause when tab is hidden (performance)
  document.addEventListener('visibilitychange', () => {
    paused = document.hidden;
    if (!paused) animate();
  });

  init();
  animate();

  return {
    destroy() {
      cancelAnimationFrame(animId);
      canvas.remove();
    },
    pause()  { paused = true;  cancelAnimationFrame(animId); },
    resume() { paused = false; animate(); },
  };
}
