// --- 1. PARTÍCULAS DE FUNDO ---
(function() {
    const canvas = document.createElement('canvas');
    canvas.id = 'signup-particles-canvas';
    document.body.prepend(canvas);
    const ctx = canvas.getContext('2d');
    let particles = []; let mouse = { x: null, y: null, radius: 150 };
    let W = 0, H = 0; let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let isDark = document.documentElement.getAttribute('data-theme') !== 'light';

    const observer = new MutationObserver(() => {
        isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    function resize() {
        W = canvas.offsetWidth; H = canvas.offsetHeight;
        canvas.width = W * dpr; canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        initParticles();
    }
    function initParticles() {
        particles = []; const count = Math.min(Math.floor((W * H) / 12000), 100);
        for (let i = 0; i < count; i++) {
            particles.push({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4, r: Math.random() * 1.5 + 0.5 });
        }
    }
    function draw() {
        ctx.clearRect(0, 0, W, H);
        const pColor = isDark ? '52, 211, 153' : '5, 150, 105';
        const pAlpha = isDark ? 0.4 : 0.6; const lineAlpha = isDark ? 0.15 : 0.25;
        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;
            if (mouse.x != null) {
                let dx = mouse.x - p.x; let dy = mouse.y - p.y; let dist = Math.hypot(dx, dy);
                if (dist < mouse.radius) {
                    let force = (mouse.radius - dist) / mouse.radius;
                    p.x -= (dx / dist) * force * 2; p.y -= (dy / dist) * force * 2;
                }
            }
            ctx.beginPath(); ctx.fillStyle = `rgba(${pColor}, ${pAlpha})`; ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
        });
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                let dx = particles[i].x - particles[j].x; let dy = particles[i].y - particles[j].y; let dist = Math.hypot(dx, dy);
                if (dist < 120) {
                    ctx.beginPath(); ctx.strokeStyle = `rgba(${pColor}, ${lineAlpha})`; ctx.lineWidth = 1;
                    ctx.moveTo(particles[i].x, particles[i].y); ctx.lineTo(particles[j].x, particles[j].y); ctx.stroke();
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

// Checkout demonstrativo: nenhuma transação financeira.
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[action*="signup"]');
    const modal = document.getElementById('checkout-modal');
    if (!form || !modal) return;
    let confirmed = false;
    form.addEventListener('submit', event => {
        const plan = form.querySelector('input[name="plano_id"]:checked');
        if (!plan || plan.dataset.free === 'true' || confirmed) return;
        event.preventDefault();
        modal.classList.add('active');
    });
    modal.querySelector('.close-checkout').addEventListener('click', () => modal.classList.remove('active'));
    ['card', 'pix'].forEach(method => {
        document.getElementById('tab-' + method).addEventListener('click', () => {
            ['card', 'pix'].forEach(item => {
                document.getElementById('tab-' + item).classList.toggle('active', item === method);
                document.getElementById('content-' + item).classList.toggle('active', item === method);
            });
        });
    });
    modal.querySelectorAll('.btn-pay').forEach(button => button.addEventListener('click', () => {
        if (confirmed || !form.reportValidity()) return;
        confirmed = true;
        modal.querySelectorAll('.btn-pay').forEach(item => item.disabled = true);
        form.requestSubmit();
    }));
});
