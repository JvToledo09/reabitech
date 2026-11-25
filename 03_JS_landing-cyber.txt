(function() {
    'use strict';

    // 1. INJEÇÃO DO CANVAS DE PARTÍCULAS
    const canvas = document.createElement('canvas');
    canvas.id = 'landing-particles-canvas';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (REDUCED_MOTION) { canvas.style.display = 'none'; return; }

    let particles = [];
    let mouse = { x: null, y: null, radius: 150 };
    let W = 0, H = 0;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    // Detectar tema (Light/Dark) em tempo real
    let isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const observer = new MutationObserver(() => {
        isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    function resize() {
        W = canvas.offsetWidth;
        H = canvas.offsetHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        initParticles();
    }

    function initParticles() {
        particles = [];
        const count = Math.min(Math.floor((W * H) / 12000), 100);
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                r: Math.random() * 1.5 + 0.5
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        
        // Light Mode: Partículas mais escuras e com alta opacidade para aparecer no fundo branco
        const pColor = isDark ? '52, 211, 153' : '5, 150, 105'; 
        const pAlpha = isDark ? 0.4 : 0.6;
        const lineAlpha = isDark ? 0.15 : 0.25;

        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;

            if (mouse.x != null) {
                let dx = mouse.x - p.x;
                let dy = mouse.y - p.y;
                let dist = Math.hypot(dx, dy);
                if (dist < mouse.radius) {
                    let force = (mouse.radius - dist) / mouse.radius;
                    p.x -= (dx / dist) * force * 2;
                    p.y -= (dy / dist) * force * 2;
                }
            }
            ctx.beginPath();
            ctx.fillStyle = `rgba(${pColor}, ${pAlpha})`;
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
        });

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                let dx = particles[i].x - particles[j].x;
                let dy = particles[i].y - particles[j].y;
                let dist = Math.hypot(dx, dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(${pColor}, ${lineAlpha})`;
                    ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', e => {
        mouse.x = e.clientX; mouse.y = e.clientY;
    });
    window.addEventListener('mouseleave', () => { mouse.x = null; mouse.y = null; });

    resize();
    draw();

    // 2. TILT 3D SUAVE NO CARD DO JOÃO SILVA
    const heroCard = document.getElementById('heroCard');
    if (heroCard) {
        const wrapper = heroCard.parentElement;
        wrapper.addEventListener('mousemove', (e) => {
            const rect = wrapper.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            // Limita a rotação a 4 graus
            const rotY = Math.max(Math.min(x * 10, 4), -4);
            const rotX = Math.max(Math.min(-y * 10, 4), -4);
            heroCard.style.transform = `perspective(1000px) rotateY(${rotY}deg) rotateX(${rotX}deg) scale(1.02)`;
        });
        wrapper.addEventListener('mouseleave', () => {
            heroCard.style.transform = `perspective(1000px) rotateY(0deg) rotateX(0deg) scale(1)`;
        });
    }
})();
