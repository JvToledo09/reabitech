(function() {
    'use strict';

    // Só roda se estiver no modo Dark para não pesar no Light
    const getTheme = () => document.documentElement.getAttribute('data-theme') || 'light';
    let isDark = getTheme() === 'dark';

    const observer = new MutationObserver(() => {
        isDark = getTheme() === 'dark';
        if (canvas) canvas.style.display = isDark ? 'block' : 'none';
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    if (!isDark) return; // Se for Light mode, nem cria o canvas

    const canvas = document.createElement('canvas');
    canvas.id = 'dashboard-particles-canvas';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (REDUCED_MOTION) { canvas.style.display = 'none'; return; }

    let particles = [];
    let mouse = { x: null, y: null, radius: 120 };
    let W = 0, H = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
        W = canvas.offsetWidth; H = canvas.offsetHeight;
        canvas.width = W * dpr; canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        initParticles();
    }

    function initParticles() {
        particles = [];
        const count = Math.min(Math.floor((W * H) / 15000), 70); // Menos partículas que o login
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * W, y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
                r: Math.random() * 1.5 + 0.5
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        const pColor = '52, 211, 153';
        const pAlpha = 0.25; // Bem sutil para não ofuscar
        const lineAlpha = 0.08;

        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;

            if (mouse.x != null) {
                let dx = mouse.x - p.x; let dy = mouse.y - p.y;
                let dist = Math.hypot(dx, dy);
                if (dist < mouse.radius) {
                    let force = (mouse.radius - dist) / mouse.radius;
                    p.x -= (dx / dist) * force * 1.5; p.y -= (dy / dist) * force * 1.5;
                }
            }
            ctx.beginPath(); ctx.fillStyle = `rgba(${pColor}, ${pAlpha})`;
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
        });

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                let dx = particles[i].x - particles[j].x;
                let dy = particles[i].y - particles[j].y;
                let dist = Math.hypot(dx, dy);
                if (dist < 120) {
                    ctx.beginPath(); ctx.strokeStyle = `rgba(${pColor}, ${lineAlpha})`; ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y); ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
    window.addEventListener('mouseleave', () => { mouse.x = null; mouse.y = null; });
    resize(); draw();
})();
