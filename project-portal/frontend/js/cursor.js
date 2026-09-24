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

  // Create canvas for magic sparkle particles
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
  const colors = [
    '#d4af37', // Gold
    '#f5d77f', // Pale gold
    '#ffffff', // Sparkle white
    '#60a5fa', // Blue spell spark
    '#facc15', // Bright yellow
  ];

  let lastX = 0;
  let lastY = 0;
  let throttle = 0;

  class Sparkle {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 1.6 + 0.4;
      this.vx = Math.cos(angle) * speed;
      this.vy = Math.sin(angle) * speed - 0.3; // subtle float up
      this.size = Math.random() * 3 + 1.5;
      this.alpha = 1;
      this.decay = Math.random() * 0.03 + 0.02;
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
      ctx.shadowBlur = 6;
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

  document.addEventListener('mousemove', (e) => {
    const x = e.clientX;
    const y = e.clientY;
    const dist = Math.hypot(x - lastX, y - lastY);

    if (dist > 4 && ++throttle % 2 === 0) {
      // Spawn 1 to 2 sparkles at cursor tip
      const count = Math.min(3, Math.floor(dist / 10) + 1);
      for (let i = 0; i < count; i++) {
        particles.push(new Sparkle(x + (Math.random() - 0.5) * 6, y + (Math.random() - 0.5) * 6));
      }
      lastX = x;
      lastY = y;
    }
  }, { passive: true });

  let animFrameId = null;

  function render() {
    ctx.clearRect(0, 0, width, height);

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.update();
      if (p.alpha <= 0.02 || p.size <= 0.2) {
        particles.splice(i, 1);
      } else {
        p.draw(ctx);
      }
    }

    animFrameId = requestAnimationFrame(render);
  }

  render();
})();
