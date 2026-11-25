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

// --- 2. LÓGICA DO FORMULÁRIO E CHECKOUT ---
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form[action*="signup"]');
    const checkoutModal = document.getElementById('checkout-modal');
    const closeCheckout = document.querySelector('.close-checkout');
    const planRadios = document.querySelectorAll('input[name="plano_id"]');
    
    // Controle de Abas no Modal
    const tabCard = document.getElementById('tab-card');
    const tabPix = document.getElementById('tab-pix');
    const contentCard = document.getElementById('content-card');
    const contentPix = document.getElementById('content-pix');

    if(tabCard && tabPix) {
        tabCard.addEventListener('click', () => {
            tabCard.classList.add('active'); tabPix.classList.remove('active');
            contentCard.classList.add('active'); contentPix.classList.remove('active');
        });
        tabPix.addEventListener('click', () => {
            tabPix.classList.add('active'); tabCard.classList.remove('active');
            contentPix.classList.add('active'); contentCard.classList.remove('active');
        });
    }

    // Interceptar envio do form
    if(form) {
        form.addEventListener('submit', (e) => {
            const selectedPlan = document.querySelector('input[name="plano_id"]:checked');
            if(!selectedPlan) return; // Deixa o Django validar

            const card = selectedPlan.nextElementSibling;
            const isFree = card.textContent.includes('Grátis');

            if(isFree) {
                // Se for grátis, envia direto
                return;
            } else {
                // Se for pago, trava o form e abre o modal
                e.preventDefault();
                checkoutModal.classList.add('active');
            }
        });
    }

    // Fechar modal
    if(closeCheckout) {
        closeCheckout.addEventListener('click', () => {
            checkoutModal.classList.remove('active');
        });
    }

    // Simular Pagamento (Cartão / PIX)
    document.querySelectorAll('.btn-pay').forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.add('loading');
            this.innerHTML = '<i class="fas fa-spinner"></i> Processando...';
            
            // Simula um delay de 2 segundos para dar realismo
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-check"></i> Aprovado!';
                this.style.background = '#059669';
                
                // Após 1 segundo, envia o formulário de verdade
                setTimeout(() => {
                    if(form) form.submit();
                }, 1000);
            }, 2000);
        });
    });
});

// Copiar PIX
window.copyPix = function() {
    const pixInput = document.getElementById('pix-code');
    pixInput.select(); pixInput.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(pixInput.value);
    const btn = document.querySelector('.btn-copy');
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i>';
    setTimeout(() => { btn.innerHTML = original; }, 2000);
};
