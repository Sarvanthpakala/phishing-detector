/* Lightweight canvas particle field with connecting lines — ambient
   cybersecurity "network scan" atmosphere. Respects reduced-motion. */
(function () {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let particles = [];
  let w, h;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  const COUNT = Math.min(70, Math.floor((window.innerWidth * window.innerHeight) / 22000));

  function makeParticle() {
    return {
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.6 + 0.6,
    };
  }
  particles = Array.from({ length: COUNT }, makeParticle);

  function isLight() {
    return document.documentElement.getAttribute('data-theme') === 'light';
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);
    const dotColor = isLight() ? 'rgba(10,13,20,0.35)' : 'rgba(0,229,199,0.55)';
    const lineColor = isLight() ? 'rgba(10,13,20,' : 'rgba(0,229,199,';

    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = dotColor;
      ctx.fill();
    }

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 130) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = lineColor + (1 - dist / 130) * 0.18 + ')';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    if (!prefersReduced) requestAnimationFrame(draw);
  }

  draw();
})();
