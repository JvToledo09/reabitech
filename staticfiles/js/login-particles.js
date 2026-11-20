/* ==============================================================================
   REABITECH - LOGIN PARTICLES
   Canvas 3D com particulas conectadas + interacao do mouse
   ============================================================================== */

(function() {
    'use strict';

    const canvas = document.getElementById('loginParticles');
    if (!canvas) return;

    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (REDUCED_MOTION) {
        canvas.style.display = 'none';
        return;
    }

    const ctx = canvas.getContext('2d');
    const TOUCH = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

    let particles = [];
    let mouse = { x: null, y: null, radius: TOUCH ? 0 : 140 };
    let W = 0, H = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
        W = canvas.offsetWidth;
        H = canvas.offsetHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        initParticles();
    }

    function initParticles() {
        const area = W * H;
        // Densidade: menos particulas em telas pequenas
        let count = Math.min(Math.floor(area / 14000), 90);
        if (TOUCH) count = Math.floor(count * 0.5);
        if (W < 600) count = Math.floor(count * 0.7);

        particles = [];
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.35,
                vy: (Math.random() - 0.5) * 0.35,
                r: Math.random() * 1.8 + 0.8,
                baseR: 0,
            });
            particles[i].baseR = particles[i].r;
        }
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);

        // Atualiza posicoes
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            // Bounce nas bordas
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;

            // Interacao com mouse
            if (mouse.x !== null && !TOUCH) {
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.hypot(dx, dy);
                if (dist < mouse.radius) {
                    const force = (mouse.radius - dist) / mouse.radius;
                    const angle = Math.atan2(dy, dx);
                    p.x -= Math.cos(angle) * force * 2.2;
                    p.y -= Math.sin(angle) * force * 2.2;
                    p.r = p.baseR * (1 + force * 1.5);
                } else {
                    p.r += (p.baseR - p.r) * 0.08;
                }
            } else {
                p.r += (p.baseR - p.r) * 0.08;
            }
        });

        // Desenha conexoes
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.hypot(dx, dy);

                if (dist < 140) {
                    const opacity = (1 - dist / 140) * 0.18;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(52, 211, 153, ${opacity})`;
                    ctx.lineWidth = 0.8;
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }

        // Desenha particulas
        particles.forEach(p => {
            const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
            gradient.addColorStop(0, 'rgba(167, 243, 208, 0.9)');
            gradient.addColorStop(0.4, 'rgba(52, 211, 153, 0.5)');
            gradient.addColorStop(1, 'rgba(52, 211, 153, 0)');

            ctx.beginPath();
            ctx.fillStyle = gradient;
            ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.fillStyle = 'rgba(167, 243, 208, 0.9)';
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
        });

        requestAnimationFrame(draw);
    }

    // Eventos
    window.addEventListener('resize', resize);

    if (!TOUCH) {
        window.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
        });

        window.addEventListener('mouseleave', () => {
            mouse.x = null;
            mouse.y = null;
        });
    }

    // Init
    resize();
    draw();

    console.log('[Login] Particulas iniciadas:', particles.length, 'particulas');
})();
